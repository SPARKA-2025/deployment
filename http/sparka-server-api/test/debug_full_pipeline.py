#!/usr/bin/env python3
import cv2
import numpy as np
import sys
import os

# Add the parent directory to the path to import server modules
sys.path.append('/app')

# Import the process_image function from server
from server import process_image, detect_vehicles, detect_plate, extract_plate_text

def test_full_pipeline():
    print("=== TESTING FULL PIPELINE ===")
    
    # Load test image
    image_path = '/app/saved_images/test2.jpg'
    print(f"Loading image from: {image_path}")
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image from {image_path}")
        return
    
    print(f"✅ Image loaded successfully, shape: {image.shape}")
    
    # Test full pipeline
    print("\n=== TESTING PROCESS_IMAGE FUNCTION ===")
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
    else:
        print("❌ No predictions returned")
        
        # Let's debug step by step
        print("\n=== DEBUGGING STEP BY STEP ===")
        
        # Step 1: Vehicle detection
        print("Step 1: Vehicle detection")
        vehicles = detect_vehicles(image)
        print(f"Vehicles found: {len(vehicles)}")
        
        if vehicles:
            vehicle = vehicles[0]
            print(f"First vehicle: {vehicle}")
            
            # Step 2: Extract vehicle image
            vx1, vy1, vx2, vy2 = vehicle['x1'], vehicle['y1'], vehicle['x2'], vehicle['y2']
            orig_vx1, orig_vy1 = int(vx1), int(vy1)
            orig_vx2, orig_vy2 = int(vx2), int(vy2)
            
            print(f"Vehicle coordinates: ({orig_vx1}, {orig_vy1}) to ({orig_vx2}, {orig_vy2})")
            
            vehicle_img = image[orig_vy1:orig_vy2, orig_vx1:orig_vx2]
            print(f"Vehicle image shape: {vehicle_img.shape}")
            
            # Step 3: Plate detection
            print("\nStep 2: Plate detection")
            plate_detections = detect_plate(vehicle_img)
            print(f"Plate detections shape: {plate_detections.shape}")
            print(f"Plate detections: {plate_detections}")
            
            if len(plate_detections) > 0:
                # Step 4: Extract plate image and OCR
                print("\nStep 3: Plate extraction and OCR")
                x1, y1, x2, y2 = int(plate_detections[0][0]), int(plate_detections[0][1]), int(plate_detections[0][2]), int(plate_detections[0][3])
                print(f"Plate coordinates in vehicle: ({x1}, {y1}) to ({x2}, {y2})")
                
                plate_img = vehicle_img[y1:y2, x1:x2]
                print(f"Plate image shape: {plate_img.shape}")
                
                if plate_img.size > 0:
                    plate_text = extract_plate_text(plate_img)
                    print(f"OCR result: '{plate_text}'")
                else:
                    print("❌ Plate image is empty")
            else:
                print("❌ No plates detected")
        else:
            print("❌ No vehicles detected")
    
    return predictions

if __name__ == "__main__":
    test_full_pipeline()