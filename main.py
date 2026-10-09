import os
import json
import sqlite3
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from core.ocr_engine import extract_document_details
from core.image_resizer import compress_and_resize_image

app = FastAPI(
    title="BharatForm Universal Multi-Platform API",
    version="4.0",
    description="Backend engine for Laptop Chrome Extension and Mobile Application"
)

# Enable CORS for Mobile Apps and Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
DB_FILE = "bharatform.db"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT UNIQUE,
            data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def read_root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"status": "online", "message": "BharatForm API Engine is Operational"}

# Multi-Document Upload & Processing API (Used by Mobile App & Web Dashboard)
@app.post("/api/v1/build-master-profile")
async def build_master_profile(files: List[UploadFile] = File(...)):
    master_profile = {
        "personal_details": {},
        "educational_details": {},
        "identity_documents": {},
        "other_certificates": []
    }

    for file in files:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        try:
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            extracted = extract_document_details(file_location)
            
            if isinstance(extracted, dict) and "error" not in extracted:
                doc_type = extracted.get("document_type", "Other Document")
                
                if any(k in doc_type for k in ["Aadhaar", "PAN", "Voter", "Passport"]):
                    master_profile["identity_documents"][doc_type] = extracted
                    if "name" in extracted and not master_profile["personal_details"].get("name"):
                        master_profile["personal_details"]["name"] = extracted.get("name")
                    if "date_of_birth" in extracted:
                        master_profile["personal_details"]["date_of_birth"] = extracted.get("date_of_birth")
                    if "gender" in extracted:
                        master_profile["personal_details"]["gender"] = extracted.get("gender")
                elif any(k in doc_type for k in ["Marksheet", "Certificate", "Degree"]):
                    master_profile["educational_details"][doc_type] = extracted
                else:
                    master_profile["other_certificates"].append(extracted)

        except Exception as e:
            continue
        finally:
            if os.path.exists(file_location):
                os.remove(file_location)

    student_name = master_profile["personal_details"].get("name", "Default_Student")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO profiles (student_name, data) VALUES (?, ?)
        ON CONFLICT(student_name) DO UPDATE SET data=excluded.data, created_at=CURRENT_TIMESTAMP
    ''', (student_name, json.dumps(master_profile)))
    conn.commit()
    conn.close()

    return {"success": True, "student_name": student_name, "master_profile": master_profile}

# Get Saved Profile API (Used by Chrome Extension & Mobile App)
@app.get("/api/v1/get-latest-profile")
def get_latest_profile():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM profiles ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"success": True, "profile": json.loads(row["data"])}
    return {"success": False, "message": "No profile found in database"}

# Image Resizer API Endpoint (For Photo/Signature Compression)
@app.post("/api/v1/compress-image")
async def compress_image(
    file: UploadFile = File(...),
    max_kb: int = Form(50),
    width: int = Form(300),
    height: int = Form(300)
):
    input_location = os.path.join(UPLOAD_DIR, file.filename)
    output_filename = f"compressed_{file.filename}"
    output_location = os.path.join(PROCESSED_DIR, output_filename)

    try:
        with open(input_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        res = compress_and_resize_image(input_location, output_location, max_kb, width, height)
        if res["success"]:
            return {
                "success": True,
                "details": res,
                "file_url": f"/download/{output_filename}"
            }
        return {"success": False, "error": res["error"]}
    finally:
        if os.path.exists(input_location):
            os.remove(input_location)

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(PROCESSED_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)