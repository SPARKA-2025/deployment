import time
from flask import Flask, request, jsonify
import numpy as np
import cv2
import math
import os
from ultralytics import YOLO
from paddleocr import PaddleOCR
from sort import Sort
from secrets import token_urlsafe
import requests
import json
from flask_cors import CORS
import grpc

import detection_pb2
import detection_pb2_grpc
import vehicle_detection_pb2
import vehicle_detection_pb2_grpc
import plate_text_extraction_pb2
import plate_text_extraction_pb2_grpc

app = Flask(__name__)
CORS(app)

channelPlate = grpc.insecure_channel('localhost:50051')
stubPlate = detection_pb2_grpc.PlateDetectionStub(channelPlate)

channelVehicle = grpc.insecure_channel('localhost:50052')
stubVehicle = vehicle_detection_pb2_grpc.VehicleDetectionStub(channelVehicle)

channelOCR = grpc.insecure_channel('localhost:50053')
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

    upload_image(image, filename, object_storage_server)
    status_code = send_to_server(payload, server_url)
    return status_code

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
    metadata = response.plates[0]
    plate_detections = np.vstack((np.empty((0, 5)), [metadata.x1,metadata.y1,metadata.x2,metadata.y2,metadata.confidence]))

    return plate_detections

def extract_plate_text(image):
    _, img_encoded = cv2.imencode('.jpg', image)
    image_data = img_encoded.tobytes()
    response = stubOCR.Extract(plate_text_extraction_pb2.ImageRequest(image_data=image_data))
    return response.text

    # result = ocr.ocr(image, cls=True)
    # if result is None or len(result) == 0 or result[0] is None:
    #     return "No text detected"
    # try:
    #     return ''.join([res[1][0] for res in result[0]])
    # except Exception as e:
    #     print(f"Error extracting text: {e}")
    #     return "Error during text extraction"


def process_image(image):
    vehicle_detections = detect_vehicles(image)
    print(vehicle_detections)
    print(type(vehicle_detections))
    predictions = []
    plate_tracker = tracker
    processed_ids = PROCESSED_IDS

    for vehicle in vehicle_detections:
        vx1, vy1, vx2, vy2 = vehicle['x1'], vehicle['y1'], vehicle['x2'], vehicle['y2']
        vehicle_img = image[int(vy1):int(vy2), int(vx1):int(vx2)]
        
        plate_detections = detect_plate(vehicle_img)

        print(plate_detections)
        print(type(plate_detections))

        results_tracker = plate_tracker.update(plate_detections)

        for result in results_tracker:
            x1, y1, x2, y2, id = result
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cx, cy = x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2

            try:
                px1, py1, px2, py2 = plate_detections[0][0], plate_detections[0][1], plate_detections[0][2], plate_detections[0][3]
                rpx1, rpy1, rpx2, rpy2 = vehicle['x1'] + px1, vehicle['y1'] + py1, vehicle['x1'] + px2, vehicle['y1'] + py2
                print(rpx1, rpy1, rpx2, rpy2)
                x_condition = 600<(rpx1+rpx2)/2<1100
                y_condition = 500<(rpy1+rpy2)/2<800
                print(x_condition, y_condition)
                if not x_condition or not y_condition:
                    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                    metadata = {
                        "vehicle_class": vehicle['class'],
                        "plate_number": 'No Detection',
                        "vehicle_position": {"x1": vehicle['x1'], "y1": vehicle['y1'], "x2": vehicle['x2'], "y2": vehicle['y2']},
                        "plate_position": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                        "status": {"x": str(x_condition), "y": str(y_condition)},
                        "position": [rpx1, rpy1, rpx2, rpy2]
                    }

                    request_influxdb_gateway(metadata, image)
                    print("belum masuk persyaratan")
                    break
            except:
                print("hasil deteksinya tidak ada", plate_detections)

            if id not in processed_ids:
                processed_ids[id] = True
                plate_img = vehicle_img[y1:y2, x1:x2]
                plate_text = extract_plate_text(plate_img)

                if plate_text:
                    predictions.append({
                        "vehicle_class": vehicle['class'],
                        "plate_number": plate_text,
                        "vehicle_position": {"x1": vehicle['x1'], "y1": vehicle['y1'], "x2": vehicle['x2'], "y2": vehicle['y2']},
                        "plate_position": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                        "status": {"x": str(x_condition), "y": str(y_condition)},
                        "position": [rpx1, rpy1, rpx2, rpy2]
                    })

                    # Identify closest vehicle and save image
                    closest_vehicle_distance = float('inf')
                    closest_vehicle_img = None

                    for v in vehicle_detections:
                        vx1, vy1, vx2, vy2 = v['x1'], v['y1'], v['x2'], v['y2']
                        vcx, vcy = (vx1 + vx2) // 2, (vy1 + vy2) // 2
                        distance = math.sqrt((cx - vcx) ** 2 + (cy - vcy) ** 2)
                        if distance < closest_vehicle_distance:
                            closest_vehicle_distance = distance
                            closest_vehicle_img = image[int(vy1):int(vy2), int(vx1):int(vx2)]

                    if closest_vehicle_img is not None:
                        vehicle_filename = f"{plate_text}.jpg"
                        vehicle_filepath = os.path.join(SAVE_DIR, vehicle_filename)
                        cv2.imwrite(vehicle_filepath, closest_vehicle_img)
                        print(f"Saved closest vehicle image: {vehicle_filepath}")

    return predictions

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    image_file = request.files['image']
    image = np.frombuffer(image_file.read(), np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    predictions = process_image(image)

    if len(predictions) != 0:
        prediction_metadata = predictions[0]

        request_influxdb_gateway(prediction_metadata, image)

    return jsonify(predictions)

@app.route('/performance', methods=['GET'])
def get_performance():
    now_time = time.time()
    image = cv2.imread('image.jpg')
    predictions = process_image(image)
    elapsed_time = time.time() - now_time
    score = 1/elapsed_time
    
    return jsonify({
        'elapsed_time': elapsed_time,
        'score': score
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
