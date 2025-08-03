#!/usr/bin/env python3
import cv2
import numpy as np
import sys
import os

# Add the parent directory to the path to import server modules
sys.path.append('/app')

# Import the process_image function from server
from server import process_image

def test_with_larger_image():
    print("=== TESTING WITH LARGER IMAGE ===")
    
    # Use a larger image
    image_path = '/app/saved_images/1962DQ_1753372679.jpg'
    print(f"Loading image from: {image_path}")
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image from {image_path}")
        return
    
    print(f"✅ Image loaded successfully, shape: {image.shape}")
    
    # Test full pipeline
    print("\n=== TESTING PROCESS_IMAGE WITH LARGER IMAGE ===")
    predictions = process_image(image, debug=True)
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Number of predictions: {len(predictions)}")
    
    if predictions:
        for i, prediction in enumerate(predictions):
            print(f"\nPrediction {i+1}:")
            print(f"  - Vehicle class: {prediction.get('vehicle_class', 'N/A')}")
            print(f"  - Plate number: {prediction.get('plate_number', 'N/A')}")
            print(f"  - Vehicle position: {prediction.get('vehicle_position', 'N/A')}")
            print(f"  - Plate position: {prediction.get('plate_position', 'N/A')}")
            print(f"  - Status: {prediction.get('status', 'N/A')}")
        print("\n✅ Pipeline working successfully!")
    else:
        print("❌ No predictions returned")
    
    return predictions

if __name__ == "__main__":
    test_with_larger_image()