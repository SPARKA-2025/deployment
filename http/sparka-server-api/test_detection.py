import requests
import os
import json

# Test the plate detection API
def test_plate_detection():
    api_url = "http://localhost:5000/predict"
    saved_images_dir = "c:\\xampp\\htdocs\\sparka\\deployment\\saved_images"
    
    # Get list of image files
    image_files = [f for f in os.listdir(saved_images_dir) if f.endswith('.jpg')]
    
    print(f"Found {len(image_files)} image files to test")
    
    successful_detections = 0
    total_tests = min(5, len(image_files))  # Test only first 5 images
    
    for i, image_file in enumerate(image_files[:total_tests]):
        image_path = os.path.join(saved_images_dir, image_file)
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(api_url, files=files)
                
            if response.status_code == 200:
                result = response.json()
                print(f"\nTest {i+1}: {image_file}")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                if result and len(result) > 0:
                    for detection in result:
                        plate_number = detection.get('plate_number', '')
                        if plate_number and plate_number != 'No text detected':
                            print(f"✅ Detected plate: {plate_number}")
                            successful_detections += 1
                        else:
                            print(f"❌ No valid plate detected")
                else:
                    print(f"❌ No detections returned")
            else:
                print(f"❌ API error for {image_file}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing {image_file}: {e}")
    
    print(f"\n=== Test Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Successful detections: {successful_detections}")
    print(f"Success rate: {successful_detections/total_tests*100:.1f}%")

if __name__ == "__main__":
    test_plate_detection()