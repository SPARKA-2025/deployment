#!/usr/bin/env python3
import requests
import cv2
import json
import time

def test_endpoint_with_test2():
    print("=== TESTING /predict ENDPOINT WITH test2.jpg ===")
    
    # Server URL
    server_url = "http://localhost:5000"
    
    # Health check first
    print("Checking server health...")
    try:
        health_response = requests.get(f"{server_url}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Server health check passed")
        else:
            print(f"❌ Server health check failed: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return
    
    # Load and send test2.jpg
    image_path = "../../../saved_images/test2.jpg"  # Relative path from test directory
    
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        print(f"\nLoaded image: {image_path}")
        print(f"Image size: {len(image_data)} bytes")
        
        # Prepare request
        files = {'image': ('test2.jpg', image_data, 'image/jpeg')}
        
        print("\nSending request to /predict endpoint...")
        start_time = time.time()
        
        response = requests.post(f"{server_url}/predict", files=files, timeout=30)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n=== PREDICTION RESULT ===")
            print(json.dumps(result, indent=2))
            
            if result:
                print(f"\n✅ Success! Found {len(result)} predictions")
                for i, pred in enumerate(result):
                    print(f"Prediction {i+1}:")
                    print(f"  - Vehicle: {pred.get('vehicle_class', 'N/A')}")
                    print(f"  - Plate: {pred.get('plate_number', 'N/A')}")
            else:
                print("\n❌ Empty result (no predictions)")
        else:
            print(f"\n❌ Request failed: {response.text}")
            
    except FileNotFoundError:
        print(f"❌ Image file not found: {image_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_endpoint_with_test2()