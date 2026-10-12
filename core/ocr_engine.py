import os
import base64
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def extract_document_details(file_path: str):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY is not set in .env file."}

    client = Groq(api_key=api_key)

    try:
        with open(file_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        return {"error": f"Error reading image file: {str(e)}"}

    mime_type = "image/jpeg"
    if file_path.lower().endswith(".png"):
        mime_type = "image/png"
    elif file_path.lower().endswith(".webp"):
        mime_type = "image/webp"

    data_url = f"data:{mime_type};base64,{encoded_image}"

    prompt = """
    You are an expert Indian Document Parsing AI. 
    1. Identify the type of document (e.g., "Aadhaar Card", "PAN Card", "10th Marksheet", "12th Marksheet", "Graduation Marksheet", "Passport Photo", "Signature", "Other Certificate").
    2. Extract all relevant structured fields into a clean JSON object.
    
    Format requirements:
    - Return ONLY valid JSON wrapped in ```json ```.
    - Do not add conversational text.
    """

    try:
        completion = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        raw_content = completion.choices[0].message.content
        
        # Clean JSON String
        cleaned = re.sub(r'```json\s*|\s*```', '', raw_content).strip()
        parsed_json = json.loads(cleaned)
        return parsed_json

    except Exception as e:
        return {"error": f"Groq Vision OCR Error: {str(e)}"}