import requests
import json

def test_predict_endpoint():
    url = 'http://localhost:5000/predict'
    
    # Test with tt2.jpg
    with open('tt2.jpg', 'rb') as f:
        files = {'image': ('tt2.jpg', f, 'image/jpeg')}
        
        print("Sending request to /predict endpoint...")
        response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\n=== PREDICTION RESULT ===")
                print(json.dumps(result, indent=2))
                
                if result:
                    print(f"\nFound {len(result)} predictions:")
                    for i, pred in enumerate(result):
                        print(f"\nPrediction {i+1}:")
                        print(f"  Vehicle Class: {pred.get('vehicle_class', 'N/A')}")
                        print(f"  Plate Number: {pred.get('plate_number', 'N/A')}")
                        print(f"  Vehicle Position: {pred.get('vehicle_position', 'N/A')}")
                        print(f"  Plate Position: {pred.get('plate_position', 'N/A')}")
                        print(f"  Status: {pred.get('status', 'N/A')}")
                else:
                    print("\nNo predictions returned (empty array)")
                    print("This could mean:")
                    print("1. No vehicles detected")
                    print("2. No plates detected on vehicles")
                    print("3. OCR failed to extract text")
                    print("4. Tracker filtered out detections")
                    
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"Error response: {response.text}")

if __name__ == '__main__':
    test_predict_endpoint()