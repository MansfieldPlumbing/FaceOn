# faceonstudioutils.py

import os
from PIL import Image

def preprocess_source_images(directory: str, max_width: int = 640, max_height: int = 480):
    """
    Scans a directory for images and resizes them in place if they exceed the max dimensions.
    """
    print(f"INFO: Pre-processing images in '{directory}'...")
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    resized_count = 0
    
    for filename in os.listdir(directory):
        if not filename.lower().endswith(supported_extensions):
            continue
            
        filepath = os.path.join(directory, filename)
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                if width > max_width or height > max_height:
                    print(f"  - Resizing {filename} ({width}x{height})")
                    img.thumbnail((max_width, max_height), Image.LANCZOS)
                    # Convert to RGB if it's RGBA to avoid issues with JPEG format
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    img.save(filepath)
                    resized_count += 1
        except Exception as e:
            print(f"WARN: Could not process file {filename}. Error: {e}")
            
    if resized_count > 0:
        print(f"INFO: Resized {resized_count} image(s).")
    else:
        print("INFO: All images are within the size limit. No resizing needed.")