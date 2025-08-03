import time
from flask import Flask, request, jsonify
import numpy as np
import cv2
import math
import os
import base64
# from ultralytics import YOLO
# from paddleocr import PaddleOCR
from sort import Sort
from secrets import token_urlsafe
import requests
import json
from flask_cors import CORS
import grpc
import pika

import detection_pb2
import detection_pb2_grpc
import vehicle_detection_pb2
import vehicle_detection_pb2_grpc
import plate_text_extraction_pb2
import plate_text_extraction_pb2_grpc

app = Flask(__name__)
CORS(app)

# Get gRPC URLs from environment variables
GRPC_VEHICLE_HOST = os.getenv('GRPC_VEHICLE_HOST', 'sparka-grpc-vehicle-dev')
GRPC_VEHICLE_PORT = os.getenv('GRPC_VEHICLE_PORT', '50051')
GRPC_PLATE_HOST = os.getenv('GRPC_PLATE_HOST', 'sparka-grpc-plate-dev')
GRPC_PLATE_PORT = os.getenv('GRPC_PLATE_PORT', '50053')
GRPC_OCR_HOST = os.getenv('GRPC_OCR_HOST', 'sparka-grpc-ocr-dev')
GRPC_OCR_PORT = os.getenv('GRPC_OCR_PORT', '50052')

GRPC_VEHICLE_URL = f'{GRPC_VEHICLE_HOST}:{GRPC_VEHICLE_PORT}'
GRPC_PLATE_URL = f'{GRPC_PLATE_HOST}:{GRPC_PLATE_PORT}'
GRPC_OCR_URL = f'{GRPC_OCR_HOST}:{GRPC_OCR_PORT}'

channelVehicle = grpc.insecure_channel(GRPC_VEHICLE_URL)
stubVehicle = vehicle_detection_pb2_grpc.VehicleDetectionStub(channelVehicle)

channelPlate = grpc.insecure_channel(GRPC_PLATE_URL)
stubPlate = detection_pb2_grpc.PlateDetectionStub(channelPlate)

channelOCR = grpc.insecure_channel(GRPC_OCR_URL)
stubOCR = plate_text_extraction_pb2_grpc.PlateTextExtractionStub(channelOCR)

# Configuration
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
SAVE_DIR = "saved_images"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# Initialize models
# ocr = PaddleOCR(lang='en', det=True, rec=True, use_angle_cls=False, det_db_unclip_ratio=1.2, det_db_box_thresh=0.1, drop_score=0.6, max_text_length=9)
# plate_model = YOLO("model/updated_model3.pt")
# vehicle_model = YOLO("model/yolov8n.pt")
  
tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)

# Constants
# CLASS_NAMES = ["plat"]
# VEHICLE_CLASS_NAMES = vehicle_model.names
PROCESSED_IDS = {}

server_url = "http://influxdb_gateway:5000/save"
object_storage_server = "http://minio_gateway:5002/upload"

def request_influxdb_gateway(prediction_metadata, image):
    time_now = str(int(time.time()*10000000))
    filename = f'{prediction_metadata["vehicle_class"]}-{prediction_metadata["plate_number"]}-{time_now}-{token_urlsafe(32)}'

    payload = {
        "measurement": "plate_detection",
        "fields": {
            "plate_position_x": (prediction_metadata['plate_position']['x1'] + prediction_metadata['plate_position']['x2'])/2,
            "plate_position_y": (prediction_metadata['plate_position']['y1'] + prediction_metadata['plate_position']['y2'])/2,
            "vehicle_position_x": (prediction_metadata['vehicle_position']['x1'] + prediction_metadata['vehicle_position']['x2'])/2,
            "vehicle_position_y": (prediction_metadata['vehicle_position']['y1'] + prediction_metadata['vehicle_position']['y2'])/2,
            "plate_number": prediction_metadata["plate_number"],
            "vehicle_class": prediction_metadata["vehicle_class"],
            "filename": filename,
        },
        "tags": {
            "vehicle_class": prediction_metadata["vehicle_class"],
            "plate_number": prediction_metadata["plate_number"],
            "id": time_now,
        }
    }

    # upload_image(image, filename, object_storage_server)
    send_image(image, filename, 'amqp://sparka:sparka123@rabbitmq:5672/')
    send_to_rabbitmq(payload)
    # status_code = send_to_server(payload, server_url)
    return 200

def send_to_server(data, server_url):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(server_url, data=json.dumps(data), headers=headers)
    return response.status_code

def upload_image(image, image_name, server_url):
    # Convert the image to JPEG format
    _, image_encoded = cv2.imencode('.jpg', image)
    
    # Send the encoded image in a POST request
    files = {'image': (f'{image_name}.jpg', image_encoded.tobytes(), 'image/jpeg')}
    response = requests.post(f"{server_url}", files=files)
    
    if response.status_code == 200:
        print("Upload successful:", response.json())
    else:
        print("Upload failed:", response.json())

def send_image(image, image_name, rabbitmq_url):
    # Read the image
    _, image_encoded = cv2.imencode('.jpg', image)
    
    # Encode the image bytes in base64
    image_base64 = base64.b64encode(image_encoded.tobytes()).decode('utf-8')
    
    # Establish connection with RabbitMQ
    connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    channel = connection.channel()
    
    # Declare the queue
    channel.queue_declare(queue='image_queue')
    
    # Send the message (image + metadata)
    message = {
        'image_name': image_name,
        'image': image_base64
    }
    channel.basic_publish(exchange='', routing_key='image_queue', body=json.dumps(message))
    
    print(f" [x] Sent image {image_name}")
    connection.close()

def send_to_rabbitmq(data, queue_name='data_queue'):
    connection = pika.BlockingConnection(pika.URLParameters('amqp://sparka:sparka123@rabbitmq:5672/'))
    channel = connection.channel()
    
    # Declare the queue
    channel.queue_declare(queue=queue_name)
    
    # Send data to the queue
    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=json.dumps(data),
                          properties=pika.BasicProperties(
                              content_type='application/json',
                          ))
    
    print(" [x] Sent data to RabbitMQ")
    connection.close()

def preprocess_image(image):
    """Preprocess image for vehicle detection with 2x resize"""
    try:
        # Get original dimensions
        height, width = image.shape[:2]
        
        # Resize to 2x for better vehicle detection
        target_height = height * 2
        target_width = width * 2
        
        # Use INTER_CUBIC for better quality upscaling
        resized = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
        
        return resized
        
    except Exception as e:
        print(f"Error in preprocess_image: {e}")
        return image

def detect_vehicles(image):
    try:
        print(f"[DEBUG] Starting vehicle detection...")
        # Apply preprocessing (2x resize) for better vehicle detection
        preprocessed_image = preprocess_image(image)
        print(f"[DEBUG] Image preprocessed, shape: {preprocessed_image.shape}")
        
        _, img_encoded = cv2.imencode('.jpg', preprocessed_image)
        image_data = img_encoded.tobytes()
        print(f"[DEBUG] Image encoded, size: {len(image_data)} bytes")

        print(f"[DEBUG] Calling gRPC vehicle detection at {GRPC_VEHICLE_URL}")
        response = stubVehicle.Detect(vehicle_detection_pb2.ImageRequest(image_data=image_data))
        print(f"[DEBUG] gRPC response received, vehicles count: {len(response.vehicles)}")

        # Display results and scale coordinates back to original image size
        detections = []
        for vehicle in response.vehicles:
            # Scale coordinates back from 2x to original size
            detection = {
                'x1': vehicle.x1 / 2,
                'y1': vehicle.y1 / 2,
                'x2': vehicle.x2 / 2,
                'y2': vehicle.y2 / 2,
                'class': vehicle.detected_class,
                'confidence': vehicle.confidence,
            }
            detections.append(detection)
            print(f"[DEBUG] Vehicle detected: {detection}")
        
        print(f"[DEBUG] Total vehicles detected: {len(detections)}")
        return detections
    except Exception as e:
        print(f"[ERROR] Vehicle detection failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def preprocess_vehicle_for_plate(vehicle_img):
    """Preprocess vehicle image for better plate detection"""
    try:
        height, width = vehicle_img.shape[:2]
        print(f"[DEBUG] Vehicle image original size: {width}x{height}")
        
        # If vehicle image is too small, resize it for better plate detection
        min_size = 100  # Minimum size for effective plate detection
        if width < min_size or height < min_size:
            # Calculate scale factor to make the smaller dimension at least min_size
            scale_factor = max(min_size / width, min_size / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            print(f"[DEBUG] Resizing vehicle image from {width}x{height} to {new_width}x{new_height} (scale: {scale_factor:.2f})")
            resized = cv2.resize(vehicle_img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            return resized, scale_factor
        else:
            print(f"[DEBUG] Vehicle image size is adequate, no resizing needed")
            return vehicle_img, 1.0
            
    except Exception as e:
        print(f"Error in preprocess_vehicle_for_plate: {e}")
        return vehicle_img, 1.0

def detect_plate(vehicle_img):
    try:
        print(f"[DEBUG] Starting plate detection on vehicle image shape: {vehicle_img.shape}")
        
        # Preprocess vehicle image for better plate detection
        processed_vehicle, scale_factor = preprocess_vehicle_for_plate(vehicle_img)
        print(f"[DEBUG] Vehicle image preprocessed, shape: {processed_vehicle.shape}, scale: {scale_factor}")
        
        _, img_encoded = cv2.imencode('.jpg', processed_vehicle)
        image_data = img_encoded.tobytes()
        print(f"[DEBUG] Vehicle image encoded, size: {len(image_data)} bytes")
        
        print(f"[DEBUG] Calling gRPC plate detection at {GRPC_PLATE_URL}")
        response = stubPlate.Detect(detection_pb2.ImageRequest(image_data=image_data))
        print(f"[DEBUG] gRPC plate response received, plates count: {len(response.plates)}")
        
        try:
            metadata = response.plates[0]
            # Scale coordinates back to original vehicle image size
            scaled_x1 = metadata.x1 / scale_factor
            scaled_y1 = metadata.y1 / scale_factor
            scaled_x2 = metadata.x2 / scale_factor
            scaled_y2 = metadata.y2 / scale_factor
            
            plate_detections = np.vstack((np.empty((0, 5)), [scaled_x1, scaled_y1, scaled_x2, scaled_y2, metadata.confidence]))
            print(f"[DEBUG] Plate detected (scaled back): [{scaled_x1}, {scaled_y1}, {scaled_x2}, {scaled_y2}, {metadata.confidence}]")
        except:
            plate_detections = np.empty((0, 5))
            print(f"[DEBUG] No plates detected")
        
        print(f"[DEBUG] Total plates detected: {len(plate_detections)}")
        return plate_detections
    except Exception as e:
        print(f"[ERROR] Plate detection failed: {e}")
        import traceback
        traceback.print_exc()
        return np.empty((0, 5))

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
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(resized)
        
        # Light sharpening
        kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return sharpened
        
    except Exception as e:
        print(f"Error in enhance_plate_for_ocr: {e}")
        return plate_img

def extract_plate_text(image):
    """Extract text from plate image with enhanced preprocessing"""
    try:
        print(f"[DEBUG] Starting OCR on plate image shape: {image.shape}")
        # Apply enhanced preprocessing
        enhanced_image = enhance_plate_for_ocr(image)
        print(f"[DEBUG] Plate image enhanced, shape: {enhanced_image.shape}")
        
        # Encode enhanced image
        _, img_encoded = cv2.imencode('.jpg', enhanced_image)
        image_data = img_encoded.tobytes()
        print(f"[DEBUG] Enhanced plate image encoded, size: {len(image_data)} bytes")
        
        # Extract text using OCR service
        print(f"[DEBUG] Calling gRPC OCR service at {GRPC_OCR_URL}")
        response = stubOCR.Extract(plate_text_extraction_pb2.ImageRequest(image_data=image_data))
        print(f"[DEBUG] OCR response received, text: '{response.text}'")
        
        return response.text
    except Exception as e:
        print(f"[ERROR] OCR extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return ""

# jika terjadi kemacetan maka debug = false 
def process_image(image, debug=True):
    # Use preprocessed image (2x resize) for vehicle detection
    vehicle_detections = detect_vehicles(image)
    print(f"Vehicle detections: {len(vehicle_detections)}")
    
    if not vehicle_detections:
        print("No vehicles detected, skipping frame to optimize performance")
        # OPTIMASI: Skip frame ketika tidak ada kendaraan terdeteksi
        # Ini menghemat resource computational dan meningkatkan performa untuk video streaming
        # dengan banyak frame kosong tanpa kendaraan
        return []
    
    print(f"Vehicle detections found: {len(vehicle_detections)}")
    for i, vehicle in enumerate(vehicle_detections):
        print(f"Vehicle {i}: {vehicle}")
    
    predictions = []
    # Create new tracker instance for each request to avoid ID conflicts
    plate_tracker = Sort(max_age=20, min_hits=1, iou_threshold=0.3)  # Reduced min_hits to 1
    processed_ids = {}  # Use local processed_ids instead of global

    for vehicle_idx, vehicle in enumerate(vehicle_detections):
        vx1, vy1, vx2, vy2 = vehicle['x1'], vehicle['y1'], vehicle['x2'], vehicle['y2']
        # Use original coordinates (no scaling needed)
        orig_vx1, orig_vy1 = int(vx1), int(vy1)
        orig_vx2, orig_vy2 = int(vx2), int(vy2)
        
        vehicle_img = image[orig_vy1:orig_vy2, orig_vx1:orig_vx2]
        
        plate_detections = detect_plate(vehicle_img)

        # If no plates detected, still add vehicle detection without plate info
        if len(plate_detections) == 0:
            print(f"[DEBUG] No plates detected for vehicle {vehicle_idx}, adding vehicle-only detection")
            predictions.append({
                "vehicle_class": vehicle['class'],
                "plate_number": "No plate detected",
                "vehicle_position": {"x1": orig_vx1, "y1": orig_vy1, "x2": orig_vx2, "y2": orig_vy2},
                "plate_position": {"x1": 0, "y1": 0, "x2": 0, "y2": 0},
                "status": {"x": "true", "y": "true"},
                "position": [0, 0, 0, 0]
            })
            continue

        results_tracker = plate_tracker.update(plate_detections)

        for result in results_tracker:
            x1, y1, x2, y2, id = result
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cx, cy = x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2

            # Calculate plate position for metadata (optional)
            try:
                px1, py1, px2, py2 = plate_detections[0][0], plate_detections[0][1], plate_detections[0][2], plate_detections[0][3]
                # Use original coordinates for plate position calculation
                rpx1, rpy1, rpx2, rpy2 = orig_vx1 + px1, orig_vy1 + py1, orig_vx1 + px2, orig_vy1 + py2
                print(f"Plate position: {rpx1}, {rpy1}, {rpx2}, {rpy2}")
                # Remove strict position filtering to allow all detections
                x_condition = True  # Accept all x positions
                y_condition = True  # Accept all y positions
                print(f"Position conditions: x={x_condition}, y={y_condition}")
            except Exception as e:
                print("Error calculating plate position:", plate_detections, e)
                # Set default values if calculation fails
                rpx1, rpy1, rpx2, rpy2 = 0, 0, 0, 0
                x_condition = True
                y_condition = True

            if id not in processed_ids:
                processed_ids[id] = True
                
                plate_img = vehicle_img[y1:y2, x1:x2]
                plate_text = extract_plate_text(plate_img)

                # Always add detection, even if OCR fails
                final_plate_text = plate_text if plate_text else "No text detected"
                predictions.append({
                    "vehicle_class": vehicle['class'],
                    "plate_number": final_plate_text,
                    "vehicle_position": {"x1": orig_vx1, "y1": orig_vy1, "x2": orig_vx2, "y2": orig_vy2},
                    "plate_position": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "status": {"x": str(x_condition), "y": str(y_condition)},
                    "position": [rpx1, rpy1, rpx2, rpy2]
                })

                # Save the current vehicle image that has detected plate
                if final_plate_text and final_plate_text != "No text detected":
                    # Save the vehicle image that successfully detected the plate
                    vehicle_filename = f"{final_plate_text}_{int(time.time())}.jpg"
                    vehicle_filepath = os.path.join(SAVE_DIR, vehicle_filename)
                    cv2.imwrite(vehicle_filepath, vehicle_img)
                    print(f"Saved vehicle image with detected plate: {vehicle_filepath}")
                    
                    # Also save the cropped plate image for reference
                    if plate_img.size > 0:
                        plate_filename = f"plate_{final_plate_text}_{int(time.time())}.jpg"
                        plate_filepath = os.path.join(SAVE_DIR, plate_filename)
                        cv2.imwrite(plate_filepath, plate_img)
                        print(f"Saved plate image: {plate_filepath}")
    
    return predictions

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    image_file = request.files['image']
    image = np.frombuffer(image_file.read(), np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    predictions = process_image(image)

    # Filter hanya deteksi yang berhasil (yang memiliki plate_number selain "No plate detected")
    successful_predictions = []
    for pred in predictions:
        if pred.get('plate_number') and pred['plate_number'] not in ['No plate detected', 'No text detected', '']:
            successful_predictions.append(pred)
    
    if len(successful_predictions) != 0:
        prediction_metadata = successful_predictions[0]
        request_influxdb_gateway(prediction_metadata, image)

    return jsonify(successful_predictions)

@app.route('/performance', methods=['GET'])
def get_performance():
    now_time = time.time()
    image = cv2.imread('image.jpg')
    predictions = process_image(image, debug=True)
    elapsed_time = time.time() - now_time
    score = 1/elapsed_time

    if len(predictions) != 0:
        prediction_metadata = predictions[0]
        request_influxdb_gateway(prediction_metadata, image)
    
    return jsonify({
        'elapsed_time': elapsed_time,
        'score': score
    })

@app.route('/test/<id>', methods=['GET'])
def test(id):
    now_time = time.time()
    id = str(id)
    if id == "00":
        image = cv2.imread('image_example/bawahkiri.jpg')
    elif id == "01":
        image = cv2.imread('image_example/ataskiri.jpg')
    elif id == "10":
        image = cv2.imread('image_example/bawahkanan.jpg')
    elif id == "11":
        image = cv2.imread('image_example/ataskanan.jpg')

    predictions = process_image(image, debug=True)
    elapsed_time = time.time() - now_time
    score = 1/elapsed_time

    if len(predictions) != 0:
        prediction_metadata = predictions[0]
        request_influxdb_gateway(prediction_metadata, image)
    
    return jsonify({
        'elapsed_time': elapsed_time,
        'score': score,
        'meteadata': prediction_metadata
    })



@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'message': "the server are run correctly",
        'status': "200"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
