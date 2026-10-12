import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")

if not api_key:
    raise ValueError("API Key environment variable is missing on server.")

genai.configure(api_key=api_key)

def extract_text_from_image(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        
        # Use the standard stable gemini-pro model for text/multimodal fallback if flash throws 404
        model = genai.GenerativeModel('gemini-pro-vision')
        
        prompt = (
            "You are an expert OCR and document parser. "
            "Extract all relevant details (such as Name, Father's Name, Date of Birth, "
            "Roll Number, Marks/Grades, ID Numbers, Address, etc.) from this document image "
            "and return them in a clean, structured JSON or text format."
        )
        
        response = model.generate_content([prompt, img])
        return response.text

    except Exception as e:
        # Fallback to standard gemini-1.5-pro if vision model fails
        try:
            model_fallback = genai.GenerativeModel('gemini-1.5-pro')
            response = model_fallback.generate_content([prompt, img])
            return response.text
        except Exception as err:
            raise RuntimeError(f"Gemini API Error: {str(err)}")