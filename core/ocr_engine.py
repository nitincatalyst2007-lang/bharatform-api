import os
from PIL import Image
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")

if not api_key:
    raise ValueError("API Key environment variable is missing on server.")

client = genai.Client(api_key=api_key)

def extract_text_from_image(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                img,
                "You are an expert OCR and document parser. Extract all relevant details (such as Name, Father's Name, Date of Birth, Roll Number, Marks/Grades, ID Numbers, Address, etc.) from this document image and return them in a clean, structured JSON or text format."
            ]
        )
        
        return response.text

    except Exception as e:
        except Exception as e:
        raise RuntimeError(f"Gemini API Error: {str(e)}")