import grpc
import cv2
import os
import sys
import numpy as np
from glob import glob

# Add the current directory to Python path to import protobuf files
sys.path.append('.')

try:
    import detection_pb2
    import detection_pb2_grpc
except ImportError as e:
    print(f"Error importing protobuf files: {e}")
    print("Make sure detection_pb2.py and detection_pb2_grpc.py are in the current directory")
    sys.exit(1)

def test_plate_detection():
    """Test gRPC Plate Detection Service"""
    print("=== Testing gRPC Plate Detection Service ===")
    
    # gRPC connection settings
    GRPC_PLATE_HOST = 'localhost'
    GRPC_PLATE_PORT = '50052'  # Port dari docker-compose.dev.yml
    GRPC_PLATE_URL = f'{GRPC_PLATE_HOST}:{GRPC_PLATE_PORT}'
    
    try:
        # Create gRPC channel and stub
        channel = grpc.insecure_channel(GRPC_PLATE_URL)
        stub = detection_pb2_grpc.PlateDetectionStub(channel)
        
        print(f"Connected to Plate Detection Service at {GRPC_PLATE_URL}")
        
        # Get test images from current test directory
        saved_images_dir = "."
        if not os.path.exists(saved_images_dir):
            print(f"Directory {saved_images_dir} not found!")
            return
        
        image_files = glob(os.path.join(saved_images_dir, "tt2.jpg"))  # Test tt2.jpg specifically
        
        if not image_files:
            print("No JPG images found in saved_images directory!")
            return
        
        print(f"Testing {len(image_files)} images...\n")
        
        total_detections = 0
        
        for i, image_path in enumerate(image_files, 1):
            print(f"[{i}] Testing: {os.path.basename(image_path)}")
            
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                print(f"  ❌ Failed to read image: {image_path}")
                continue
            
            # Encode image to bytes
            _, img_encoded = cv2.imencode('.jpg', image)
            image_data = img_encoded.tobytes()
            
            try:
                # Send request to gRPC service
                response = stub.Detect(detection_pb2.ImageRequest(image_data=image_data))
                
                # Process response
                plates = response.plates
                print(f"  ✅ Detected {len(plates)} plate(s)")
                
                if plates:
                    total_detections += len(plates)
                    for j, plate in enumerate(plates, 1):
                        print(f"    Plate {j}:")
                        print(f"      - Confidence: {plate.confidence:.3f}")
                        print(f"      - Bounding Box: ({plate.x1}, {plate.y1}) to ({plate.x2}, {plate.y2})")
                        print(f"      - Size: {plate.x2 - plate.x1} x {plate.y2 - plate.y1}")
                        
                        # Extract plate region for visualization
                        plate_region = image[int(plate.y1):int(plate.y2), int(plate.x1):int(plate.x2)]
                        if plate_region.size > 0:
                            print(f"      - Plate region size: {plate_region.shape[1]} x {plate_region.shape[0]}")
                else:
                    print(f"    No plates detected")
                    
            except grpc.RpcError as e:
                print(f"  ❌ gRPC Error: {e.code()} - {e.details()}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            print()
        
        print(f"=== Plate Detection Summary ===")
        print(f"Total images tested: {len(image_files)}")
        print(f"Total plates detected: {total_detections}")
        print(f"Average plates per image: {total_detections / len(image_files):.2f}")
        
        # Close gRPC channel
        channel.close()
        
    except grpc.RpcError as e:
        print(f"❌ Failed to connect to Plate Detection Service: {e.code()} - {e.details()}")
        print(f"Make sure the service is running on {GRPC_PLATE_URL}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_single_image(image_path):
    """Test plate detection on a single image"""
    print(f"=== Testing Single Image: {image_path} ===")
    
    # gRPC connection settings
    GRPC_PLATE_HOST = 'localhost'
    GRPC_PLATE_PORT = '50052'
    GRPC_PLATE_URL = f'{GRPC_PLATE_HOST}:{GRPC_PLATE_PORT}'
    
    try:
        # Create gRPC channel and stub
        channel = grpc.insecure_channel(GRPC_PLATE_URL)
        stub = detection_pb2_grpc.PlateDetectionStub(channel)
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Failed to read image: {image_path}")
            return
        
        print(f"Image size: {image.shape[1]} x {image.shape[0]}")
        
        # Encode image to bytes
        _, img_encoded = cv2.imencode('.jpg', image)
        image_data = img_encoded.tobytes()
        
        # Send request to gRPC service
        response = stub.Detect(detection_pb2.ImageRequest(image_data=image_data))
        
        # Process response
        plates = response.plates
        print(f"✅ Detected {len(plates)} plate(s)")
        
        for i, plate in enumerate(plates, 1):
            print(f"  Plate {i}:")
            print(f"    - Confidence: {plate.confidence:.3f}")
            print(f"    - Bounding Box: ({plate.x1}, {plate.y1}) to ({plate.x2}, {plate.y2})")
            print(f"    - Size: {plate.x2 - plate.x1} x {plate.y2 - plate.y1}")
            
            # Extract and save plate region
            plate_region = image[int(plate.y1):int(plate.y2), int(plate.x1):int(plate.x2)]
            if plate_region.size > 0:
                print(f"    - Plate region size: {plate_region.shape[1]} x {plate_region.shape[0]}")
                
                # Save extracted plate region
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                plate_filename = f"saved_images/extracted_plate_{base_name}_plate{i}.jpg"
                cv2.imwrite(plate_filename, plate_region)
                print(f"    - Saved plate region to: {plate_filename}")
        
        # Close gRPC channel
        channel.close()
        
    except grpc.RpcError as e:
        print(f"❌ gRPC Error: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_vehicle_crop(vehicle_image_path):
    """Test plate detection on a cropped vehicle image"""
    print(f"=== Testing Vehicle Crop: {vehicle_image_path} ===")
    
    # This function simulates what happens in server.py when a vehicle is detected
    # and the vehicle region is cropped for plate detection
    
    # gRPC connection settings
    GRPC_PLATE_HOST = 'localhost'
    GRPC_PLATE_PORT = '50052'
    GRPC_PLATE_URL = f'{GRPC_PLATE_HOST}:{GRPC_PLATE_PORT}'
    
    try:
        # Create gRPC channel and stub
        channel = grpc.insecure_channel(GRPC_PLATE_URL)
        stub = detection_pb2_grpc.PlateDetectionStub(channel)
        
        # Read image
        image = cv2.imread(vehicle_image_path)
        if image is None:
            print(f"❌ Failed to read image: {vehicle_image_path}")
            return
        
        print(f"Vehicle image size: {image.shape[1]} x {image.shape[0]}")
        
        # Encode image to bytes
        _, img_encoded = cv2.imencode('.jpg', image)
        image_data = img_encoded.tobytes()
        
        # Send request to gRPC service
        response = stub.Detect(detection_pb2.ImageRequest(image_data=image_data))
        
        # Process response
        plates = response.plates
        print(f"✅ Detected {len(plates)} plate(s) in vehicle crop")
        
        for i, plate in enumerate(plates, 1):
            print(f"  Plate {i}:")
            print(f"    - Confidence: {plate.confidence:.3f}")
            print(f"    - Bounding Box: ({plate.x1}, {plate.y1}) to ({plate.x2}, {plate.y2})")
            print(f"    - Size: {plate.x2 - plate.x1} x {plate.y2 - plate.y1}")
            
            # Extract plate region
            plate_region = image[int(plate.y1):int(plate.y2), int(plate.x1):int(plate.x2)]
            if plate_region.size > 0:
                print(f"    - Plate region size: {plate_region.shape[1]} x {plate_region.shape[0]}")
        
        # Close gRPC channel
        channel.close()
        
    except grpc.RpcError as e:
        print(f"❌ gRPC Error: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test single image if path provided
        image_path = sys.argv[1]
        if os.path.exists(image_path):
            test_single_image(image_path)
        else:
            print(f"Image file not found: {image_path}")
    else:
        # Test multiple images from saved_images directory
        test_plate_detection()