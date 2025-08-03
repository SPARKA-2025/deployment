import requests
import os
import json

def test_tt2_image():
    """Test specifically with tt2.jpg image that works in debug_pipeline.py"""
    url = 'http://localhost:5000/predict'
    
    # Use the exact same image that works in debug_pipeline.py
    image_path = '../saved_images/tt2.jpg'
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print("=== TESTING /predict WITH tt2.jpg (SAME AS debug_pipeline.py) ===")
    print("="*70)
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': ('tt2.jpg', f, 'image/jpeg')}
            
            print("Sending request to /predict endpoint...")
            response = requests.post(url, files=files, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n=== PREDICTION RESULT ===")
                print(json.dumps(result, indent=2))
                
                if result:
                    print(f"\n✅ SUCCESS: Found {len(result)} predictions")
                    for i, pred in enumerate(result):
                        print(f"  Prediction {i+1}:")
                        print(f"    Vehicle: {pred.get('vehicle_class', 'N/A')}")
                        print(f"    Plate: {pred.get('plate_number', 'N/A')}")
                        print(f"    Vehicle Position: {pred.get('vehicle_position', 'N/A')}")
                        print(f"    Plate Position: {pred.get('plate_position', 'N/A')}")
                        print(f"    Status: {pred.get('status', 'N/A')}")
                    
                    if any(pred.get('plate_number') == 'H1962DQ' for pred in result):
                        print("\n🎯 PERFECT! Found expected plate number H1962DQ")
                    else:
                        print("\n⚠️  Different plate number detected than expected (H1962DQ)")
                        
                else:
                    print("\n❌ Empty result (no predictions)")
                    print("\nPossible issues:")
                    print("1. gRPC services not responding correctly")
                    print("2. Image preprocessing differences")
                    print("3. Tracker configuration issues")
                    print("4. Port configuration problems")
                    
            else:
                print(f"\n❌ HTTP Error {response.status_code}")
                print(f"Response: {response.text}")
                
    except requests.exceptions.Timeout:
        print("❌ Request timeout - server may be overloaded")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server may be down")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_health_endpoint():
    """Test if server is responding"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Server health check passed")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server health check error: {e}")
        return False

if __name__ == '__main__':
    print("Checking server health first...")
    if test_health_endpoint():
        print("\nProceeding with tt2.jpg test...\n")
        test_tt2_image()
    else:
        print("\n❌ Server is not responding. Please check if sparka-server-api-dev is running.")
        print("Run: docker ps | Select-String sparka-server-api-dev")