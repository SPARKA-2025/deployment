import cv2
import numpy as np
import requests
import os
from PIL import Image
import matplotlib.pyplot as plt

def test_specific_image(image_path):
    """Test a specific image to debug detection issues"""
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return
    
    # Read and display image info
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not read image: {image_path}")
        return
        
    print(f"Testing image: {image_path}")
    print(f"Image shape: {image.shape}")
    
    # Send to API
    with open(image_path, 'rb') as f:
        files = {'image': f}
        try:
            response = requests.post('http://localhost:5000/predict', files=files)
            if response.status_code == 200:
                result = response.json()
                print(f"API Response: {result}")
                
                if result:
                    for i, detection in enumerate(result):
                        print(f"\nDetection {i+1}:")
                        print(f"  Vehicle class: {detection.get('vehicle_class', 'N/A')}")
                        print(f"  Plate number: {detection.get('plate_number', 'N/A')}")
                        print(f"  Vehicle position: {detection.get('vehicle_position', 'N/A')}")
                        print(f"  Plate position: {detection.get('plate_position', 'N/A')}")
                        print(f"  Status: {detection.get('status', 'N/A')}")
                else:
                    print("No detections found")
            else:
                print(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

def analyze_saved_images():
    """Analyze recently saved images to find problematic ones"""
    saved_dir = "c:\\xampp\\htdocs\\sparka\\deployment\\saved_images"
    
    if not os.path.exists(saved_dir):
        print(f"Saved images directory not found: {saved_dir}")
        return
    
    # Get all jpg files
    jpg_files = [f for f in os.listdir(saved_dir) if f.lower().endswith('.jpg')]
    
    # Look for files with '1962DQ' in the name
    problematic_files = [f for f in jpg_files if '1962DQ' in f]
    
    print(f"Found {len(problematic_files)} files with '1962DQ':")
    for file in problematic_files:
        file_path = os.path.join(saved_dir, file)
        print(f"  - {file}")
        
        # Check if it's a vehicle image (not a plate crop)
        if not file.startswith('plate_'):
            print(f"    Testing vehicle image: {file}")
            test_specific_image(file_path)
            break  # Test only the first one

if __name__ == "__main__":
    print("=== Debug Detection Analysis ===")
    print("\n1. Analyzing saved images for '1962DQ' detections...")
    analyze_saved_images()
    
    print("\n2. You can also test a specific image by calling:")
    print("   test_specific_image('path/to/your/image.jpg')")