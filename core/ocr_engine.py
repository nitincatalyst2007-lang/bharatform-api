import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv()

# Fetch API key securely from environment variables (works for both local and Render)
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")

if not api_key:
    raise ValueError("API Key environment variable is missing on server.")

# Configure the Gemini API client
genai.configure(api_key=api_key)

def extract_text_from_image(image_path: str) -> str:
    """
    Processes the given image using Google Gemini API (gemini-flash-latest) 
    to extract and structure all text details for form filling.
    """
    try:
        # Open image using Pillow
        img = Image.open(image_path)
        
        # Initialize the universal latest flash model
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Prompt instructing Gemini to act as an OCR and parser for Indian academic/ID documents
        prompt = (
            "You are an expert OCR and document parser. "
            "Extract all relevant details (such as Name, Father's Name, Date of Birth, "
            "Roll Number, Marks/Grades, ID Numbers, Address, etc.) from this document image "
            "and return them in a clean, structured JSON or text format."
        )
        
        # Generate content from the model
        response = model.generate_content([prompt, img])
        
        return response.text

    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {str(e)}")