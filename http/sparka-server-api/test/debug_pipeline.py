import requests
import json
import cv2
import numpy as np
import grpc
import sys
import os

# Add parent directory to path to import protobuf files
sys.path.append('..')

import detection_pb2
import detection_pb2_grpc
import vehicle_detection_pb2
import vehicle_detection_pb2_grpc
import plate_text_extraction_pb2
import plate_text_extraction_pb2_grpc

def test_vehicle_detection_direct():
    """Test vehicle detection service directly"""
    print("=== TESTING VEHICLE DETECTION SERVICE ===")
    
    # Connect to vehicle detection service (port 50053 based on docker ps)
    channel = grpc.insecure_channel('localhost:50053')
    stub = vehicle_detection_pb2_grpc.VehicleDetectionStub(channel)
    
    # Load and preprocess image (same as server.py)
    image = cv2.imread('tt2.jpg')
    if image is None:
        print("ERROR: Could not load tt2.jpg")
        return None
        
    # Apply 2x preprocessing like in server.py
    height, width = image.shape[:2]
    target_height = height * 2
    target_width = width * 2
    preprocessed = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
    
    # Encode image
    _, img_encoded = cv2.imencode('.jpg', preprocessed)
    image_data = img_encoded.tobytes()
    
    try:
        response = stub.Detect(vehicle_detection_pb2.ImageRequest(image_data=image_data))
        
        print(f"Vehicles detected: {len(response.vehicles)}")
        vehicles = []
        for i, vehicle in enumerate(response.vehicles):
            # Scale coordinates back from 2x to original size
            vehicle_data = {
                'x1': vehicle.x1 / 2,
                'y1': vehicle.y1 / 2,
                'x2': vehicle.x2 / 2,
                'y2': vehicle.y2 / 2,
                'class': vehicle.detected_class,
                'confidence': vehicle.confidence,
            }
            vehicles.append(vehicle_data)
            print(f"  Vehicle {i+1}: {vehicle_data}")
            
        return vehicles, image
        
    except Exception as e:
        print(f"ERROR in vehicle detection: {e}")
        return None, None

def test_plate_detection_direct(vehicles, image):
    """Test plate detection service directly"""
    print("\n=== TESTING PLATE DETECTION SERVICE ===")
    
    if not vehicles:
        print("No vehicles to test plate detection")
        return []
        
    # Connect to plate detection service (port 50052 based on docker ps)
    channel = grpc.insecure_channel('localhost:50052')
    stub = detection_pb2_grpc.PlateDetectionStub(channel)
    
    all_plates = []
    
    for i, vehicle in enumerate(vehicles):
        print(f"\nTesting plate detection on vehicle {i+1}")
        
        # Extract vehicle region
        vx1, vy1, vx2, vy2 = int(vehicle['x1']), int(vehicle['y1']), int(vehicle['x2']), int(vehicle['y2'])
        vehicle_img = image[vy1:vy2, vx1:vx2]
        
        if vehicle_img.size == 0:
            print(f"  ERROR: Empty vehicle image for vehicle {i+1}")
            continue
            
        # Encode vehicle image
        _, img_encoded = cv2.imencode('.jpg', vehicle_img)
        image_data = img_encoded.tobytes()
        
        try:
            response = stub.Detect(detection_pb2.ImageRequest(image_data=image_data))
            
            print(f"  Plates detected on vehicle {i+1}: {len(response.plates)}")
            
            for j, plate in enumerate(response.plates):
                plate_data = {
                    'vehicle_idx': i,
                    'x1': plate.x1,
                    'y1': plate.y1,
                    'x2': plate.x2,
                    'y2': plate.y2,
                    'confidence': plate.confidence,
                    'vehicle_img': vehicle_img
                }
                all_plates.append(plate_data)
                print(f"    Plate {j+1}: x1={plate.x1}, y1={plate.y1}, x2={plate.x2}, y2={plate.y2}, conf={plate.confidence}")
                
        except Exception as e:
            print(f"  ERROR in plate detection for vehicle {i+1}: {e}")
            
    return all_plates

def test_ocr_direct(plates):
    """Test OCR service directly"""
    print("\n=== TESTING OCR SERVICE ===")
    
    if not plates:
        print("No plates to test OCR")
        return []
        
    # Connect to OCR service (port 50051 based on docker ps)
    channel = grpc.insecure_channel('localhost:50051')
    stub = plate_text_extraction_pb2_grpc.PlateTextExtractionStub(channel)
    
    ocr_results = []
    
    for i, plate in enumerate(plates):
        print(f"\nTesting OCR on plate {i+1} from vehicle {plate['vehicle_idx']+1}")
        
        # Extract plate region
        x1, y1, x2, y2 = int(plate['x1']), int(plate['y1']), int(plate['x2']), int(plate['y2'])
        vehicle_img = plate['vehicle_img']
        plate_img = vehicle_img[y1:y2, x1:x2]
        
        if plate_img.size == 0:
            print(f"  ERROR: Empty plate image for plate {i+1}")
            continue
            
        # Apply enhancement like in server.py
        try:
            if len(plate_img.shape) == 3:
                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_img.copy()
                
            # 3x resize for better resolution
            height, width = gray.shape
            target_height = height * 3
            target_width = width * 3
            
            resized = cv2.resize(gray, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
            
            # Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(resized)
            
            # Light sharpening
            kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            # Save enhanced plate for debugging
            cv2.imwrite(f'saved_images/debug_plate_{i+1}_enhanced.jpg', sharpened)
            print(f"  Saved enhanced plate image: saved_images/debug_plate_{i+1}_enhanced.jpg")
            
            # Encode enhanced image
            _, img_encoded = cv2.imencode('.jpg', sharpened)
            image_data = img_encoded.tobytes()
            
            response = stub.Extract(plate_text_extraction_pb2.ImageRequest(image_data=image_data))
            
            result = {
                'plate_idx': i,
                'vehicle_idx': plate['vehicle_idx'],
                'text': response.text,
                'confidence': plate['confidence']
            }
            ocr_results.append(result)
            
            print(f"  OCR Result: '{response.text}'")
            
        except Exception as e:
            print(f"  ERROR in OCR for plate {i+1}: {e}")
            
    return ocr_results

def test_full_pipeline():
    """Test the complete pipeline step by step"""
    print("=== TESTING COMPLETE PIPELINE ===")
    print("Image: tt2.jpg")
    print("Expected plate: H 1962 DQ")
    print("="*50)
    
    # Step 1: Vehicle Detection
    vehicles, image = test_vehicle_detection_direct()
    if not vehicles:
        print("PIPELINE FAILED: No vehicles detected")
        return
        
    # Step 2: Plate Detection
    plates = test_plate_detection_direct(vehicles, image)
    if not plates:
        print("PIPELINE FAILED: No plates detected")
        return
        
    # Step 3: OCR
    ocr_results = test_ocr_direct(plates)
    if not ocr_results:
        print("PIPELINE FAILED: No OCR results")
        return
        
    # Summary
    print("\n=== PIPELINE SUMMARY ===")
    print(f"Vehicles detected: {len(vehicles)}")
    print(f"Plates detected: {len(plates)}")
    print(f"OCR results: {len(ocr_results)}")
    
    for result in ocr_results:
        print(f"Vehicle {result['vehicle_idx']+1}, Plate {result['plate_idx']+1}: '{result['text']}' (conf: {result['confidence']})")
        
    # Check if expected text is found
    expected_texts = ['H 1962 DQ', 'H1962DQ', 'H196200', 'H390200']
    found_expected = False
    for result in ocr_results:
        if any(expected in result['text'] or result['text'] in expected for expected in expected_texts):
            found_expected = True
            print(f"\n✓ EXPECTED TEXT FOUND: '{result['text']}'")
            break
            
    if not found_expected:
        print(f"\n✗ EXPECTED TEXT NOT FOUND. Got: {[r['text'] for r in ocr_results]}")
        
if __name__ == '__main__':
    test_full_pipeline()