import requests
import json
import time

def test_predict_with_multiple_attempts():
    """Test /predict endpoint multiple times to trigger tracker"""
    url = 'http://localhost:5000/predict'
    
    print("=== TESTING /predict ENDPOINT WITH MULTIPLE ATTEMPTS ===")
    print("Note: Server uses tracker with min_hits=3, so we need multiple requests")
    print("="*60)
    
    for attempt in range(5):
        print(f"\n--- Attempt {attempt + 1} ---")
        
        with open('tt2.jpg', 'rb') as f:
            files = {'image': ('tt2.jpg', f, 'image/jpeg')}
            
            start_time = time.time()
            response = requests.post(url, files=files)
            end_time = time.time()
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {end_time - start_time:.2f}s")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"Result: {json.dumps(result, indent=2)}")
                    
                    if result:
                        print(f"✓ SUCCESS: Found {len(result)} predictions")
                        for i, pred in enumerate(result):
                            print(f"  Prediction {i+1}:")
                            print(f"    Vehicle: {pred.get('vehicle_class', 'N/A')}")
                            print(f"    Plate: {pred.get('plate_number', 'N/A')}")
                            print(f"    Vehicle Position: {pred.get('vehicle_position', 'N/A')}")
                            print(f"    Plate Position: {pred.get('plate_position', 'N/A')}")
                        return result
                    else:
                        print("✗ Empty result (tracker may need more hits)")
                        
                except json.JSONDecodeError as e:
                    print(f"JSON Error: {e}")
                    print(f"Raw response: {response.text}")
            else:
                print(f"HTTP Error: {response.text}")
                
        # Small delay between attempts
        if attempt < 4:
            time.sleep(0.5)
            
    print("\n=== SUMMARY ===")
    print("No successful detections after 5 attempts.")
    print("This suggests the tracker's min_hits=3 requirement is not being met.")
    return None

def test_single_request():
    """Test single request to /predict"""
    url = 'http://localhost:5000/predict'
    
    print("\n=== SINGLE REQUEST TEST ===")
    
    with open('tt2.jpg', 'rb') as f:
        files = {'image': ('tt2.jpg', f, 'image/jpeg')}
        
        response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Result: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"Error: {response.text}")
            return None

if __name__ == '__main__':
    # Test single request first
    single_result = test_single_request()
    
    # If single request fails, try multiple attempts
    if not single_result:
        test_predict_with_multiple_attempts()
    else:
        print("\n✓ Single request was successful!")