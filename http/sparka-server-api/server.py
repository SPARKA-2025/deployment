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
GRPC_VEHICLE_HOST = os.getenv('GRPC_VEHICLE_HOST', 'grpc-vehicle')
GRPC_VEHICLE_PORT = os.getenv('GRPC_VEHICLE_PORT', '50053')
GRPC_PLATE_HOST = os.getenv('GRPC_PLATE_HOST', 'grpc-plate')
GRPC_PLATE_PORT = os.getenv('GRPC_PLATE_PORT', '50052')
GRPC_OCR_HOST = os.getenv('GRPC_OCR_HOST', 'grpc-ocr')
GRPC_OCR_PORT = os.getenv('GRPC_OCR_PORT', '50051')

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
    resized_image = cv2.resize(image, (image.shape[1] * 2, image.shape[0] * 2))
    gray_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    return blurred_image

def detect_vehicles(image):
    _, img_encoded = cv2.imencode('.jpg', image)
    image_data = img_encoded.tobytes()

    response = stubVehicle.Detect(vehicle_detection_pb2.ImageRequest(image_data=image_data))

    # Display results
    detections = []
    for vehicle in response.vehicles:
        detections.append({
            'x1': vehicle.x1,
            'y1': vehicle.y1,
            'x2': vehicle.x2,
            'y2': vehicle.y2,
            'class': vehicle.detected_class,
            'confidence': vehicle.confidence,
        })
    return detections

def detect_plate(vehicle_img):
    _, img_encoded = cv2.imencode('.jpg', vehicle_img)
    image_data = img_encoded.tobytes()
    response = stubPlate.Detect(detection_pb2.ImageRequest(image_data=image_data))
    try:
        metadata = response.plates[0]
        plate_detections = np.vstack((np.empty((0, 5)), [metadata.x1,metadata.y1,metadata.x2,metadata.y2,metadata.confidence]))
    except:
        plate_detections = np.empty((0, 5))

    return plate_detections

def extract_plate_text(image):
    try:
        _, img_encoded = cv2.imencode('.jpg', image)
        image_data = img_encoded.tobytes()
        
        # Add timeout for gRPC call
        response = stubOCR.Extract(
            plate_text_extraction_pb2.ImageRequest(image_data=image_data),
            timeout=10.0  # 10 second timeout
        )
        return response.text
    except grpc.RpcError as e:
        print(f"gRPC error in OCR extraction: {e}")
        return ""
    except Exception as e:
        print(f"Error in OCR extraction: {e}")
        return ""

def process_image(image, debug=False):
    vehicle_detections = detect_vehicles(image)
    predictions = []
    plate_tracker = tracker
    processed_ids = PROCESSED_IDS

    for vehicle in vehicle_detections:
        vx1, vy1, vx2, vy2 = vehicle['x1'], vehicle['y1'], vehicle['x2'], vehicle['y2']
        vehicle_img = image[int(vy1):int(vy2), int(vx1):int(vx2)]
        
        plate_detections = detect_plate(vehicle_img)

        results_tracker = plate_tracker.update(plate_detections)

        # Process each detected plate directly
        for i, plate_detection in enumerate(plate_detections):
            try:
                px1, py1, px2, py2, confidence = plate_detection[:5]
                px1, py1, px2, py2 = int(px1), int(py1), int(px2), int(py2)
                
                # Calculate absolute position in original image
                rpx1 = int(vehicle['x1'] + px1)
                rpy1 = int(vehicle['y1'] + py1) 
                rpx2 = int(vehicle['x1'] + px2)
                rpy2 = int(vehicle['y1'] + py2)
                
                print(f"Plate detection {i}: confidence={confidence}, pos=({rpx1},{rpy1},{rpx2},{rpy2})")
                
                # Check if plate region is valid
                if px2 > px1 and py2 > py1 and px1 >= 0 and py1 >= 0:
                    # Extract plate image from vehicle region
                    plate_img = vehicle_img[py1:py2, px1:px2]
                    
                    if plate_img.size > 0:
                        # Extract text from plate
                        plate_text = extract_plate_text(plate_img)
                        print(f"Extracted plate text: '{plate_text}'")
                        
                        # Only add if we got valid text (minimum 3 characters)
                        if plate_text and len(plate_text.strip()) >= 3:
                            predictions.append({
                                "vehicle_class": vehicle['class'],
                                "plate_number": plate_text.strip(),
                                "vehicle_position": {"x1": vehicle['x1'], "y1": vehicle['y1'], "x2": vehicle['x2'], "y2": vehicle['y2']},
                                "plate_position": {"x1": rpx1, "y1": rpy1, "x2": rpx2, "y2": rpy2},
                                "confidence": float(confidence),
                                "plate_index": i
                            })
                            print(f"Added prediction: {plate_text.strip()}")
                            
                            # Optionally save vehicle image with detected plate
                            try:
                                vehicle_filename = f"vehicle_{plate_text.strip().replace(' ', '_')}.jpg"
                                vehicle_filepath = os.path.join(SAVE_DIR, vehicle_filename)
                                cv2.imwrite(vehicle_filepath, vehicle_img)
                                print(f"Saved vehicle image: {vehicle_filepath}")
                            except Exception as save_error:
                                print(f"Failed to save vehicle image: {save_error}")
                        else:
                            print(f"Rejected plate text (too short or empty): '{plate_text}'")
                    else:
                        print(f"Empty plate image region for detection {i}")
                else:
                    print(f"Invalid plate coordinates for detection {i}: ({px1},{py1},{px2},{py2})")
                    
            except Exception as e:
                print(f"Error processing plate detection {i}: {e}")
                continue

    return predictions

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No image file selected"}), 400
    
    try:
        # Read image data
        image_data = image_file.read()
        if len(image_data) == 0:
            return jsonify({"error": "Empty image file"}), 400
        
        # Convert to numpy array and decode
        image_array = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({"error": "Invalid image format"}), 400
        
        print(f"Image shape: {image.shape}")
        
        # Process image for predictions
        predictions = process_image(image, debug=True)
        print(f"Predictions: {predictions}")

        if len(predictions) != 0:
            prediction_metadata = predictions[0]
            request_influxdb_gateway(prediction_metadata, image)

        return jsonify(predictions)
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

@app.route('/predict-rtsp-stream', methods=['POST'])
def predict_rtsp_stream():
    from flask import Response
    import time
    data = request.get_json()
    if not data or 'rtsp_url' not in data:
        return jsonify({"error": "No RTSP URL provided"}), 400
    rtsp_url = data['rtsp_url']
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return jsonify({"error": "Unable to open RTSP stream"}), 400
    def generate():
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            predictions = process_image(frame, debug=True)
            # Optionally, encode frame to JPEG and base64 for streaming
            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            yield f"data: {{\"predictions\": {json.dumps(predictions)}, \"frame\": \"{frame_b64}\"}}\n\n"
            time.sleep(0.1)  # Faster frame rate for better detection (10 FPS)
            
            if len(predictions) != 0:
                prediction_metadata = predictions[0]
                request_influxdb_gateway(prediction_metadata, frame)
        cap.release()
    return Response(generate(), mimetype='text/event-stream')

@app.route('/performance', methods=['GET'])
def get_performance():
    now_time = time.time()
    image = cv2.imread('image.jpg')
    predictions = process_image(image, debug=True)
    elapsed_time = time.time() - now_time
    score = 1/elapsed_time
    print(image.shape, elapsed_time, score)

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
    
    prediction_metadata = None
    if len(predictions) != 0:
        prediction_metadata = predictions[0]
        request_influxdb_gateway(prediction_metadata, image)
    
    return jsonify({
        'elapsed_time': elapsed_time,
        'score': score,
        'predictions': predictions,
        'meteadata': prediction_metadata
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'message': "the server are run correctly",
        'status': "200"
    })

@app.route('/process-video', methods=['POST'])
def process_video():
    try:
        # Check if video file is uploaded
        if 'video' not in request.files:
            return jsonify({"error": "No video file uploaded"}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({"error": "No video file selected"}), 400
        
        # Save uploaded video temporarily
        temp_video_path = f'/tmp/{video_file.filename}'
        video_file.save(temp_video_path)
        
        # Open video capture
        cap = cv2.VideoCapture(temp_video_path)
        if not cap.isOpened():
            # Clean up temp file
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            return jsonify({"error": "Unable to open video file"}), 400
        
        all_detections = []
        unique_plates = set()
        frame_count = 0
        processed_frames = 0
        
        print(f"Starting video processing: {temp_video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame interval for 5 frames per second
        if fps > 0:
            frame_interval = max(1, int(fps / 5))  # Process 5 frames per second
        else:
            frame_interval = 6  # Default fallback
        
        print(f"Video FPS: {fps}, Total frames: {total_frames}, Processing every {frame_interval} frames")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Process frames at 5 FPS rate
            if frame_count % frame_interval == 0:
                processed_frames += 1
                print(f"Processing frame {frame_count}/{total_frames}...")
                
                # Process frame for plate detection
                predictions = process_image(frame, debug=True)
                
                if predictions:
                    for pred in predictions:
                        plate_number = pred.get('plate_number', '')
                        if plate_number:
                            unique_plates.add(plate_number)
                            pred['frame_number'] = frame_count
                            pred['timestamp'] = frame_count / fps if fps > 0 else frame_count
                            all_detections.append(pred)
                            print(f"Frame {frame_count}: Detected plate {plate_number}")
        
        cap.release()
        
        # Clean up temporary file
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        
        result = {
            "detections": all_detections,
            "parking_updates": [],
            "success": True,
            "total_frames_processed": processed_frames,
            "unique_plates": len(unique_plates)
        }
        
        print(f"Video processing completed. Processed {processed_frames} frames, found {len(unique_plates)} unique plates")
        return jsonify(result)
        
    except Exception as e:
        # Clean up temporary file in case of error
        if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        print(f"Error processing video: {str(e)}")
        return jsonify({"error": f"Error processing video: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
