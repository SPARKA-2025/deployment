#!/usr/bin/env python3
import cv2
import numpy as np
import sys
import os

# Add the parent directory to the path to import server modules
sys.path.append('/app')

# Import the detect_vehicles function from server
from server import detect_vehicles, preprocess_image

def test_vehicle_detection():
    print("=== TESTING VEHICLE DETECTION DIRECTLY ===")
    
    # Load test image
    image_path = '/app/saved_images/test2.jpg'
    print(f"Loading image from: {image_path}")
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image from {image_path}")
        return
    
    print(f"✅ Image loaded successfully, shape: {image.shape}")
    
    # Test preprocessing
    print("\n=== TESTING PREPROCESSING ===")
    preprocessed = preprocess_image(image)
    print(f"Original shape: {image.shape}")
    print(f"Preprocessed shape: {preprocessed.shape}")
    
    # Test vehicle detection
    print("\n=== TESTING VEHICLE DETECTION ===")
    detections = detect_vehicles(image)
    
    print(f"\n=== RESULTS ===")
    print(f"Number of vehicles detected: {len(detections)}")
    
    if detections:
        for i, detection in enumerate(detections):
            print(f"Vehicle {i+1}:")
            print(f"  - Class: {detection['class']}")
            print(f"  - Confidence: {detection['confidence']}")
            print(f"  - Coordinates: ({detection['x1']}, {detection['y1']}) to ({detection['x2']}, {detection['y2']})")
            
            # Check if coordinates are valid
            h, w = image.shape[:2]
            if (0 <= detection['x1'] < w and 0 <= detection['y1'] < h and 
                0 <= detection['x2'] < w and 0 <= detection['y2'] < h and
                detection['x1'] < detection['x2'] and detection['y1'] < detection['y2']):
                print(f"  - ✅ Coordinates are valid")
            else:
                print(f"  - ❌ Coordinates are invalid (image size: {w}x{h})")
    else:
        print("❌ No vehicles detected")
    
    return detections

if __name__ == "__main__":
    test_vehicle_detection()