import grpc
import cv2
import os
import sys
import numpy as np
from glob import glob

# Add the current directory to Python path to import protobuf files
sys.path.append('.')

try:
    import vehicle_detection_pb2
    import vehicle_detection_pb2_grpc
except ImportError as e:
    print(f"Error importing protobuf files: {e}")
    print("Make sure vehicle_detection_pb2.py and vehicle_detection_pb2_grpc.py are in the current directory")
    sys.exit(1)

def test_vehicle_detection():
    """Test gRPC Vehicle Detection Service"""
    print("=== Testing gRPC Vehicle Detection Service ===")
    
    # gRPC connection settings
    GRPC_VEHICLE_HOST = 'localhost'
    GRPC_VEHICLE_PORT = '50053'  # Port dari docker-compose.dev.yml
    GRPC_VEHICLE_URL = f'{GRPC_VEHICLE_HOST}:{GRPC_VEHICLE_PORT}'
    
    try:
        # Create gRPC channel and stub
        channel = grpc.insecure_channel(GRPC_VEHICLE_URL)
        stub = vehicle_detection_pb2_grpc.VehicleDetectionStub(channel)
        
        print(f"Connected to Vehicle Detection Service at {GRPC_VEHICLE_URL}")
        
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
                response = stub.Detect(vehicle_detection_pb2.ImageRequest(image_data=image_data))
                
                # Process response
                vehicles = response.vehicles
                print(f"  ✅ Detected {len(vehicles)} vehicle(s)")
                
                if vehicles:
                    total_detections += len(vehicles)
                    for j, vehicle in enumerate(vehicles, 1):
                        print(f"    Vehicle {j}:")
                        print(f"      - Class: {vehicle.detected_class}")
                        print(f"      - Confidence: {vehicle.confidence:.3f}")
                        print(f"      - Bounding Box: ({vehicle.x1}, {vehicle.y1}) to ({vehicle.x2}, {vehicle.y2})")
                        print(f"      - Size: {vehicle.x2 - vehicle.x1} x {vehicle.y2 - vehicle.y1}")
                else:
                    print(f"    No vehicles detected")
                    
            except grpc.RpcError as e:
                print(f"  ❌ gRPC Error: {e.code()} - {e.details()}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            print()
        
        print(f"=== Vehicle Detection Summary ===")
        print(f"Total images tested: {len(image_files)}")
        print(f"Total vehicles detected: {total_detections}")
        print(f"Average vehicles per image: {total_detections / len(image_files):.2f}")
        
        # Close gRPC channel
        channel.close()
        
    except grpc.RpcError as e:
        print(f"❌ Failed to connect to Vehicle Detection Service: {e.code()} - {e.details()}")
        print(f"Make sure the service is running on {GRPC_VEHICLE_URL}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_single_image(image_path):
    """Test vehicle detection on a single image"""
    print(f"=== Testing Single Image: {image_path} ===")
    
    # gRPC connection settings
    GRPC_VEHICLE_HOST = 'localhost'
    GRPC_VEHICLE_PORT = '50053'
    GRPC_VEHICLE_URL = f'{GRPC_VEHICLE_HOST}:{GRPC_VEHICLE_PORT}'
    
    try:
        # Create gRPC channel and stub
        channel = grpc.insecure_channel(GRPC_VEHICLE_URL)
        stub = vehicle_detection_pb2_grpc.VehicleDetectionStub(channel)
        
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
        response = stub.Detect(vehicle_detection_pb2.ImageRequest(image_data=image_data))
        
        # Process response
        vehicles = response.vehicles
        print(f"✅ Detected {len(vehicles)} vehicle(s)")
        
        for i, vehicle in enumerate(vehicles, 1):
            print(f"  Vehicle {i}:")
            print(f"    - Class: {vehicle.detected_class}")
            print(f"    - Confidence: {vehicle.confidence:.3f}")
            print(f"    - Bounding Box: ({vehicle.x1}, {vehicle.y1}) to ({vehicle.x2}, {vehicle.y2})")
            print(f"    - Size: {vehicle.x2 - vehicle.x1} x {vehicle.y2 - vehicle.y1}")
        
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
        test_vehicle_detection()