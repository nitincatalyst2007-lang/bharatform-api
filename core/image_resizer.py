import os
from PIL import Image

def compress_and_resize_image(input_path: str, output_path: str, max_kb: int = 50, target_width: int = 300, target_height: int = 300):
    """
    Resizes and compresses an image (Photo/Signature) under a specified file size limit in KB.
    """
    try:
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Resize image maintaining target dimensions
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            quality = 95
            img.save(output_path, "JPEG", quality=quality)
            
            # Reduce quality iteratively until file size is under max_kb
            while os.path.getsize(output_path) > max_kb * 1024 and quality > 10:
                quality -= 5
                img.save(output_path, "JPEG", quality=quality)
                
        return {
            "success": True,
            "final_size_kb": round(os.path.getsize(output_path) / 1024, 2),
            "dimensions": f"{target_width}x{target_height}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}