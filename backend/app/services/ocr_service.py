from PIL import Image
import os


def open_image_with_pillow(file_path: str):
    

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image not found: {file_path}")

    img = Image.open(file_path)
    
