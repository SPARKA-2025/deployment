import requests
import json

def test_predict_endpoint():
    """Test the /predict endpoint with tt2.jpg"""
    url = 'http://localhost:5000/predict'
    
    try:
        # Open and send the image file
        with open('tt2.jpg', 'rb') as f:
            files = {'image': f}
            response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\n=== PREDICTION RESULT ===")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # Check if vehicle was detected and saved
                if 'vehicles' in result:
                    print(f"\nVehicles detected: {len(result['vehicles'])}")
                    for i, vehicle in enumerate(result['vehicles'], 1):
                        print(f"Vehicle {i}:")
                        if 'plate_text' in vehicle:
                            print(f"  - Plate Text: {vehicle['plate_text']}")
                        if 'saved_filename' in vehicle:
                            print(f"  - Saved as: {vehicle['saved_filename']}")
                            
            except json.JSONDecodeError:
                print("Response is not valid JSON:")
                print(response.text)
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Failed to connect to server. Make sure the server is running on http://localhost:5000")
    except FileNotFoundError:
        print("❌ Image file 'tt2.jpg' not found in current directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_predict_endpoint()