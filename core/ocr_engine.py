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
        
        # Automatically find a supported generative model to prevent 404 errors
        target_model_name = 'gemini-1.5-flash'
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name:
                    target_model_name = m.name
                    break

        model = genai.GenerativeModel(target_model_name)
        
        prompt = (
            "You are an expert OCR and document parser. "
            "Extract all relevant details (such as Name, Father's Name, Date of Birth, "
            "Roll Number, Marks/Grades, ID Numbers, Address, etc.) from this document image "
            "and return them in a clean, structured JSON or text format."
        )
        
        response = model.generate_content([prompt, img])
        return response.text

    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {str(e)}")