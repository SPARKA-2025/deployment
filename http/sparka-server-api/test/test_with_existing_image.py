import requests
import json
import os

def test_predict_with_existing_images():
    """Test /predict endpoint with images that previously worked"""
    url = 'http://localhost:5000/predict'
    
    # List of images that should have successful detections
    test_images = [
        '../saved_images/tt2.jpg',
        '../saved_images/tt1.jpg', 
        '../saved_images/tt3.jpg',
        '../saved_images/test4.jpg',
        '../saved_images/test5.jpg'
    ]
    
    print("=== TESTING /predict WITH EXISTING SUCCESSFUL IMAGES ===")
    print("="*60)
    
    for image_path in test_images:
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            continue
            
        print(f"\n--- Testing: {os.path.basename(image_path)} ---")
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
                
                response = requests.post(url, files=files)
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result:
                        print(f"✅ SUCCESS: Found {len(result)} predictions")
                        for i, pred in enumerate(result):
                            print(f"  Prediction {i+1}:")
                            print(f"    Vehicle: {pred.get('vehicle_class', 'N/A')}")
                            print(f"    Plate: {pred.get('plate_number', 'N/A')}")
                            print(f"    Confidence: {pred.get('status', 'N/A')}")
                        
                        # If we found a successful result, return it
                        return result
                    else:
                        print("❌ Empty result")
                else:
                    print(f"❌ HTTP Error: {response.text}")
                    
        except Exception as e:
            print(f"❌ Error testing {image_path}: {e}")
    
    print("\n=== SUMMARY ===")
    print("No successful detections found with any test images.")
    return None

def test_specific_working_image():
    """Test with a specific image that we know should work"""
    url = 'http://localhost:5000/predict'
    
    # Try with an image that has a clear plate number in filename
    working_images = [
        '../saved_images/H1744.jpg',
        '../saved_images/AD193GT.jpg', 
        '../saved_images/K1842JP.jpg',
        '../saved_images/S1336LF.jpg'
    ]
    
    print("\n=== TESTING WITH IMAGES THAT HAVE CLEAR PLATE NUMBERS ===")
    
    for image_path in working_images:
        if not os.path.exists(image_path):
            continue
            
        print(f"\nTesting: {os.path.basename(image_path)}")
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
                response = requests.post(url, files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    if result:
                        print(f"✅ SUCCESS with {os.path.basename(image_path)}: {result}")
                        return result
                    else:
                        print(f"❌ Empty result for {os.path.basename(image_path)}")
                        
        except Exception as e:
            print(f"Error: {e}")
    
    return None

if __name__ == '__main__':
    # Test with existing images first
    result1 = test_predict_with_existing_images()
    
    if not result1:
        # Try with specific working images
        result2 = test_specific_working_image()
        
        if not result2:
            print("\n❌ CONCLUSION: The tracker configuration (min_hits=3) is preventing")
            print("   single-request detections from being returned, even though")
            print("   the detection pipeline works correctly.")
            print("\n💡 SOLUTION: The server needs to be configured with min_hits=1")
            print("   for single image predictions, or implement a different")
            print("   tracking strategy for API requests vs video streams.")
    else:
        print("\n✅ SUCCESS: Found working configuration!")