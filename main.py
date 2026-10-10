import os
import json
import sqlite3
import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from PIL import Image
from groq import Groq

# Load environment variables
load_dotenv()

app = FastAPI(
    title="BharatForm API",
    description="Backend API for BharatForm OCR and document processing"
)

# Enable CORS for Extension and Web Frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
DB_NAME = "bharatform.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            extracted_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "BharatForm API",
        "message": "Welcome to BharatForm Backend Services!"
    }

@app.post("/process-document")
async def process_document(file: UploadFile = File(...)):
    # 1. Verify Groq API Key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or "your_groq_api_key" in api_key:
        raise HTTPException(
            status_code=500, 
            detail="GROQ_API_KEY environment variable is invalid or missing on Render server."
        )

    # 2. Validate Uploaded File Type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, 
            detail="Uploaded file must be an image format (JPG/PNG)."
        )

    try:
        # 3. Read and Process Image
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        
        # Convert image to Base64 for Groq Vision API
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # 4. Initialize Groq Client
        client = Groq(api_key=api_key)

        prompt = (
            "Extract all form-filling details from this document image (such as Name, Father's Name, Mother's Name, "
            "Date of Birth, Gender, Aadhaar/ID Number, Roll Number, Marks, Address, Category, etc.). "
            "Return ONLY a clean JSON object containing these extracted key-value pairs without any markdown formatting."
        )

        # Active Groq vision models list to try sequentially
        vision_models = [
            "llama-3.2-11b-vision-instruct",
            "llama-3.2-90b-vision-instruct",
            "llama-3.2-11b-vision",
            "llama-3.2-90b-vision"
        ]

        response_text = None
        last_error = None

        # 5. Try available vision models dynamically
        for model_name in vision_models:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    },
                                },
                            ],
                        }
                    ],
                    model=model_name,
                    temperature=0.2,
                )
                response_text = chat_completion.choices[0].message.content.strip()
                if response_text:
                    break
            except Exception as e:
                last_error = str(e)
                continue

        if not response_text:
            raise HTTPException(
                status_code=500,
                detail=f"Groq Cloud API Vision Models Failed. Last Error: {last_error}"
            )

        # Clean JSON formatting wrappers if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()

        try:
            extracted_json = json.loads(response_text)
        except Exception:
            extracted_json = {"raw_text": response_text}

        # 6. Save result to SQLite
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO processed_documents (filename, extracted_data) VALUES (?, ?)",
            (file.filename, json.dumps(extracted_json))
        )
        conn.commit()
        conn.close()

        return {
            "success": True,
            "filename": file.filename,
            "data": extracted_json
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"OCR Processing Internal Error: {str(e)}"
        )