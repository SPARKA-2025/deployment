#!/usr/bin/env python3
import cv2
import os

def check_images():
    image_dir = '/app/saved_images/'
    files = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]
    
    print(f"Found {len(files)} image files:")
    
    for f in files[:10]:  # Check first 10 files
        try:
            img = cv2.imread(os.path.join(image_dir, f))
            if img is not None:
                print(f"{f}: {img.shape}")
            else:
                print(f"{f}: Failed to load")
        except Exception as e:
            print(f"{f}: Error - {e}")

if __name__ == "__main__":
    check_images()