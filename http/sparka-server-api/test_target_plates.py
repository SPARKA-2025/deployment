import requests
import os
import json

# Test the plate detection API for specific target plates
def test_target_plates():
    api_url = "http://localhost:5000/predict"
    saved_images_dir = "c:\\xampp\\htdocs\\sparka\\deployment\\saved_images"
    
    # Target plates to look for
    target_plates = ['H1962DQ', '1962DQ', 'S1336LF', '1336LF', 'S133610', '133610']
    
    # Get list of image files
    image_files = [f for f in os.listdir(saved_images_dir) if f.endswith('.jpg')]
    
    print(f"Testing {len(image_files)} images for target plates: {target_plates}")
    print("=" * 60)
    
    successful_detections = 0
    target_detections = 0
    total_tests = 0
    
    for i, image_file in enumerate(image_files):
        image_path = os.path.join(saved_images_dir, image_file)
        total_tests += 1
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(api_url, files=files, timeout=30)
                
            if response.status_code == 200:
                result = response.json()
                
                if result and len(result) > 0:
                    successful_detections += 1
                    for detection in result:
                        plate_number = detection.get('plate_number', '')
                        vehicle_class = detection.get('vehicle_class', '')
                        
                        # Check if detected plate matches any target
                        is_target = any(target in plate_number for target in target_plates)
                        
                        if is_target:
                            target_detections += 1
                            print(f"🎯 TARGET FOUND in {image_file}:")
                            print(f"   Plate: {plate_number}")
                            print(f"   Vehicle: {vehicle_class}")
                            print(f"   Position: {detection.get('vehicle_position', {})}")
                            print()
                        elif plate_number and plate_number != 'No text detected':
                            print(f"✅ {image_file}: {plate_number} ({vehicle_class})")
                        
            else:
                print(f"❌ API error for {image_file}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing {image_file}: {e}")
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(image_files)} images...")
    
    print("\n" + "=" * 60)
    print(f"=== FINAL RESULTS ===")
    print(f"Total images tested: {total_tests}")
    print(f"Images with detections: {successful_detections}")
    print(f"Target plate detections: {target_detections}")
    print(f"Overall detection rate: {successful_detections/total_tests*100:.1f}%")
    print(f"Target detection rate: {target_detections/total_tests*100:.1f}%")
    
    if target_detections > 0:
        print(f"\n🎉 SUCCESS: Found {target_detections} target plate(s)!")
    else:
        print(f"\n⚠️  No target plates detected. Check image quality and model performance.")

if __name__ == "__main__":
    test_target_plates()