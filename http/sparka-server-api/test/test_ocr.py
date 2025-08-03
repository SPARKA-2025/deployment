import grpc
import cv2
import os
import sys
import numpy as np
from glob import glob

# Add the current directory to Python path to import protobuf files
sys.path.append('.')

try:
    import plate_text_extraction_pb2
    import plate_text_extraction_pb2_grpc
except ImportError as e:
    print(f"Error importing protobuf files: {e}")
    print("Make sure plate_text_extraction_pb2.py and plate_text_extraction_pb2_grpc.py are in the current directory")
    sys.exit(1)

def enhance_plate_for_ocr(plate_img):
    """Enhanced preprocessing with 3x resize for better OCR accuracy"""
    try:
        # Convert to grayscale if needed
        if len(plate_img.shape) == 3:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_img.copy()
        
        # 3x resize for better resolution
        height, width = gray.shape
        target_height = height * 3
        target_width = width * 3
        
        resized = cv2.resize(gray, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
        
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
        enhanced = clahe.apply(resized)
        
        # Light sharpening
        kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return sharpened
        
    except Exception as e:
        print(f"Error in enhance_plate_for_ocr: {e}")
        return plate_img

def test_ocr_service():
    """Test gRPC OCR Service"""
    print("=== Testing gRPC OCR Service ===")
    
    # gRPC connection settings
    GRPC_OCR_HOST = 'localhost'
    GRPC_OCR_PORT = '50051'  # Port dari docker-compose.dev.yml
    GRPC_OCR_URL = f'{GRPC_OCR_HOST}:{GRPC_OCR_PORT}'
    
    try:
        # Create gRPC channel and stub
        channel = grpc.insecure_channel(GRPC_OCR_URL)
        stub = plate_text_extraction_pb2_grpc.PlateTextExtractionStub(channel)
        
        print(f"Connected to OCR Service at {GRPC_OCR_URL}")
        
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
        
        successful_extractions = 0
        total_confidence = 0
        
        for i, image_path in enumerate(image_files, 1):
            print(f"[{i}] Testing: {os.path.basename(image_path)}")
            
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                print(f"  ❌ Failed to read image: {image_path}")
                continue
            
            # Enhance image for OCR (same as server.py)
            enhanced_image = enhance_plate_for_ocr(image)
            
            # Encode enhanced image to bytes
            _, img_encoded = cv2.imencode('.jpg', enhanced_image)
            image_data = img_encoded.tobytes()
            
            try:
                # Send request to gRPC service with timeout
                response = stub.Extract(
                    plate_text_extraction_pb2.ImageRequest(image_data=image_data),
                    timeout=30.0
                )
                
                # Process response
                extracted_text = response.text.strip()
                
                if extracted_text:
                    print(f"  ✅ Extracted Text: '{extracted_text}'")
                    successful_extractions += 1
                else:
                    print(f"  ⚠️  No text extracted")
                    
            except grpc.RpcError as e:
                print(f"  ❌ gRPC Error: {e.code()} - {e.details()}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            print()
        
        print(f"=== OCR Service Summary ===")
        print(f"Total images tested: {len(image_files)}")
        print(f"Successful text extractions: {successful_extractions}")
        print(f"Success rate: {(successful_extractions / len(image_files)) * 100:.1f}%")
        
        # Close gRPC channel
        channel.close()
        
    except grpc.RpcError as e:
        print(f"❌ Failed to connect to OCR Service: {e.code()} - {e.details()}")
        print(f"Make sure the service is running on {GRPC_OCR_URL}")
    except Exception as e:
        import traceback
        print(f"❌ Unexpected error: {e}")
        print(f"Error details: {traceback.format_exc()}")

def test_single_image(image_path):
    """Test OCR on a single image"""
    print(f"=== Testing Single Image: {image_path} ===")
    
    # gRPC connection settings (same as server.py)
    GRPC_OCR_HOST = os.getenv('GRPC_OCR_HOST', 'localhost')
    GRPC_OCR_PORT = os.getenv('GRPC_OCR_PORT', '50051')
    GRPC_OCR_URL = f'{GRPC_OCR_HOST}:{GRPC_OCR_PORT}'
    
    print(f"Using OCR service: {GRPC_OCR_URL}")
    
    try:
        # Create gRPC channel and stub (same as server.py)
        channel = grpc.insecure_channel(GRPC_OCR_URL)
        stub = plate_text_extraction_pb2_grpc.PlateTextExtractionStub(channel)
        
        print(f"Connected to OCR Service at {GRPC_OCR_URL}")
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Failed to read image: {image_path}")
            return
        
        print(f"Original image size: {image.shape[1]} x {image.shape[0]}")
        
        # Test both original and enhanced images
        test_cases = [
            ("Original", image),
            ("Enhanced", enhance_plate_for_ocr(image))
        ]
        
        for case_name, test_image in test_cases:
            print(f"\n--- Testing {case_name} Image ---")
            print(f"Image size: {test_image.shape[1]} x {test_image.shape[0]}")
            
            # Encode image to bytes
            _, img_encoded = cv2.imencode('.jpg', test_image)
            image_data = img_encoded.tobytes()
            
            try:
                # Send request to gRPC service
                response = stub.Extract(plate_text_extraction_pb2.ImageRequest(image_data=image_data))
                
                # Process response
                extracted_text = response.text.strip()
                
                if extracted_text:
                    print(f"✅ Extracted Text: '{extracted_text}'")
                else:
                    print(f"⚠️  No text extracted")
                    
                # Save processed image for inspection
                output_filename = f"saved_images/ocr_test_{case_name.lower()}_{os.path.splitext(os.path.basename(image_path))[0]}.jpg"
                cv2.imwrite(output_filename, test_image)
                print(f"   Saved processed image: {output_filename}")
                    
            except grpc.RpcError as e:
                print(f"❌ gRPC Error: {e.code()} - {e.details()}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Close gRPC channel
        channel.close()
        
    except grpc.RpcError as e:
        print(f"❌ Failed to connect to OCR Service: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_text_samples():
    """Test OCR with sample text images"""
    print("=== Testing OCR with Sample Text Images ===")
    
   
    
    # gRPC connection settings
    GRPC_OCR_HOST = 'localhost'
    GRPC_OCR_PORT = '50051'
    GRPC_OCR_URL = f'{GRPC_OCR_HOST}:{GRPC_OCR_PORT}'
    
    try:
        # Create gRPC channel and stub
        channel = grpc.insecure_channel(GRPC_OCR_URL)
        stub = plate_text_extraction_pb2_grpc.PlateTextExtractionStub(channel)
        
        print(f"Connected to OCR Service at {GRPC_OCR_URL}")
        
        for i, text in enumerate(sample_texts, 1):
            print(f"\n[{i}] Testing sample text: '{text}'")
            
            # Create a simple text image
            img = np.ones((60, 200, 3), dtype=np.uint8) * 255  # White background
            cv2.putText(img, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)  # Black text
            
            # Save sample image
            sample_filename = f"sample_text_{text}.jpg"
            cv2.imwrite(sample_filename, img)
            print(f"  Created sample image: {sample_filename}")
            
            # Enhance for OCR
            enhanced_img = enhance_plate_for_ocr(img)
            
            # Encode image to bytes
            _, img_encoded = cv2.imencode('.jpg', enhanced_img)
            image_data = img_encoded.tobytes()
            
            try:
                # Send request to gRPC service
                response = stub.Extract(plate_text_extraction_pb2.ImageRequest(image_data=image_data))
                
                # Process response
                extracted_text = response.text.strip()
                
                if extracted_text:
                    match_status = "✅ MATCH" if extracted_text == text else "❌ MISMATCH"
                    print(f"  {match_status} - Expected: '{text}', Got: '{extracted_text}'")
                else:
                    print(f"  ❌ No text extracted")
                    
            except grpc.RpcError as e:
                print(f"  ❌ gRPC Error: {e.code()} - {e.details()}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Close gRPC channel
        channel.close()
        
    except grpc.RpcError as e:
        print(f"❌ Failed to connect to OCR Service: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--samples":
            # Test with sample text images
            test_text_samples()
        else:
            # Test single image if path provided
            image_path = sys.argv[1]
            if os.path.exists(image_path):
                test_single_image(image_path)
            else:
                print(f"Image file not found: {image_path}")
    else:
        # Test multiple images from saved_images directory
        test_ocr_service()