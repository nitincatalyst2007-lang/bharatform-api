import os
import requests
import base64
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")

if not api_key:
    raise ValueError("API Key environment variable is missing on server.")

def extract_text_from_image(image_path: str) -> str:
    try:
        # Read image and convert to base64 for direct REST API call
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # Determine mime type
        mime_type = "image/jpeg"
        if image_path.lower().endswith(".png"):
            mime_type = "image/png"

        # Direct REST endpoint for Gemini 1.5 Flash (bypassing SDK version mismatch)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [
                    {"text": "You are an expert OCR and document parser. Extract all relevant details (Name, Father's Name, DOB, Roll Number, Marks, ID Numbers, Address, etc.) from this document image and return them in clean structured text."},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_base64
                        }
                    }
                ]
            }]
        }

        response = requests.post(url, json=payload, headers=headers)
        result = response.json()

        if "error" in result:
            raise RuntimeError(result["error"].get("message", "Unknown API Error"))

        # Extract text from response candidates
        text_output = result["candidates"][0]["content"]["parts"][0]["text"]
        return text_output

    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {str(e)}")