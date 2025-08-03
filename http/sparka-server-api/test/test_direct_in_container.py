import subprocess
import json

def test_pipeline_in_container():
    """Test the detection pipeline directly inside the container"""
    print("=== TESTING PIPELINE DIRECTLY IN CONTAINER ===")
    print("="*60)
    
    container_name = "sparka-server-api-dev"
    
    # Create a test script to run inside the container
    test_script = '''
import sys
sys.path.append('/app')
import cv2
import numpy as np
import grpc
import os

# Import the protobuf modules
import detection_pb2
import detection_pb2_grpc
import vehicle_detection_pb2
import vehicle_detection_pb2_grpc
import plate_text_extraction_pb2
import plate_text_extraction_pb2_grpc

print("[TEST] Starting pipeline test...")

# Test gRPC connections
print("[TEST] Testing gRPC connections...")
try:
    # Vehicle detection
    vehicle_channel = grpc.insecure_channel('sparka-grpc-vehicle-dev:50051')
    vehicle_stub = vehicle_detection_pb2_grpc.VehicleDetectionStub(vehicle_channel)
    print("[TEST] ✅ Vehicle gRPC connection established")
    
    # Plate detection  
    plate_channel = grpc.insecure_channel('sparka-grpc-plate-dev:50051')
    plate_stub = detection_pb2_grpc.PlateDetectionStub(plate_channel)
    print("[TEST] ✅ Plate gRPC connection established")
    
    # OCR
    ocr_channel = grpc.insecure_channel('sparka-grpc-ocr-dev:50051')
    ocr_stub = plate_text_extraction_pb2_grpc.PlateTextExtractionStub(ocr_channel)
    print("[TEST] ✅ OCR gRPC connection established")
    
except Exception as e:
    print(f"[TEST] ❌ gRPC connection failed: {e}")
    sys.exit(1)

# Test with a sample image
print("[TEST] Testing with sample image...")
try:
    # Load the test image
    image_path = '/app/saved_images/tt2.jpg'
    if os.path.exists(image_path):
        image = cv2.imread(image_path)
        print(f"[TEST] ✅ Image loaded: {image.shape}")
        
        # Test vehicle detection
        print("[TEST] Testing vehicle detection...")
        height, width = image.shape[:2]
        target_height = height * 2
        target_width = width * 2
        resized = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
        
        _, img_encoded = cv2.imencode('.jpg', resized)
        image_data = img_encoded.tobytes()
        
        response = vehicle_stub.Detect(vehicle_detection_pb2.ImageRequest(image_data=image_data))
        print(f"[TEST] ✅ Vehicle detection: {len(response.vehicles)} vehicles found")
        
        if len(response.vehicles) > 0:
            vehicle = response.vehicles[0]
            print(f"[TEST] Vehicle: {vehicle.detected_class} at [{vehicle.x1/2}, {vehicle.y1/2}, {vehicle.x2/2}, {vehicle.y2/2}]")
            
            # Extract vehicle region
            vx1, vy1, vx2, vy2 = int(vehicle.x1/2), int(vehicle.y1/2), int(vehicle.x2/2), int(vehicle.y2/2)
            vehicle_img = image[vy1:vy2, vx1:vx2]
            
            # Test plate detection
            print("[TEST] Testing plate detection...")
            _, vehicle_encoded = cv2.imencode('.jpg', vehicle_img)
            vehicle_data = vehicle_encoded.tobytes()
            
            plate_response = plate_stub.Detect(detection_pb2.ImageRequest(image_data=vehicle_data))
            print(f"[TEST] ✅ Plate detection: {len(plate_response.plates)} plates found")
            
            if len(plate_response.plates) > 0:
                plate = plate_response.plates[0]
                print(f"[TEST] Plate at [{plate.x1}, {plate.y1}, {plate.x2}, {plate.y2}]")
                
                # Extract plate region
                px1, py1, px2, py2 = int(plate.x1), int(plate.y1), int(plate.x2), int(plate.y2)
                plate_img = vehicle_img[py1:py2, px1:px2]
                
                # Test OCR
                print("[TEST] Testing OCR...")
                # Enhance plate image
                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
                height, width = gray.shape
                target_height = height * 3
                target_width = width * 3
                enhanced = cv2.resize(gray, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
                
                _, plate_encoded = cv2.imencode('.jpg', enhanced)
                plate_data = plate_encoded.tobytes()
                
                ocr_response = ocr_stub.Extract(plate_text_extraction_pb2.ImageRequest(image_data=plate_data))
                print(f"[TEST] ✅ OCR result: '{ocr_response.text}'")
                
                if ocr_response.text:
                    print(f"[TEST] 🎯 SUCCESS! Detected plate text: {ocr_response.text}")
                else:
                    print(f"[TEST] ❌ OCR returned empty text")
            else:
                print(f"[TEST] ❌ No plates detected")
        else:
            print(f"[TEST] ❌ No vehicles detected")
    else:
        print(f"[TEST] ❌ Image not found: {image_path}")
        
except Exception as e:
    print(f"[TEST] ❌ Pipeline test failed: {e}")
    import traceback
    traceback.print_exc()

print("[TEST] Pipeline test completed.")
'''
    
    try:
        # Write the test script to a temporary file and execute it in container
        result = subprocess.run([
            "docker", "exec", container_name,
            "python", "-c", test_script
        ], capture_output=True, text=True, timeout=60)
        
        print("=== CONTAINER OUTPUT ===")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("=== ERRORS ===")
            print(result.stderr)
            
        if result.returncode == 0:
            print("\n✅ Container test completed successfully")
        else:
            print(f"\n❌ Container test failed with exit code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("❌ Container test timed out")
    except Exception as e:
        print(f"❌ Error running container test: {e}")

if __name__ == '__main__':
    test_pipeline_in_container()