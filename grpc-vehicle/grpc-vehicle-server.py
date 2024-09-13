import grpc
import vehicle_detection_pb2
import vehicle_detection_pb2_grpc
import cv2
import numpy as np
from ultralytics import YOLO
from concurrent import futures
import requests
import os

# Load the initial YOLO model for vehicle detection
vehicle_model = YOLO('model/yolov8n.pt')
VEHICLE_CLASS_NAMES = vehicle_model.names


# Function to download the model from a URL
def download_model(model_url, save_path='new_vehicle_model.pt'):
    try:
        response = requests.get(model_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as model_file:
                for chunk in response.iter_content(1024):
                    model_file.write(chunk)
            return True, "Model downloaded successfully"
        else:
            return False, f"Failed to download model: {response.status_code}"
    except Exception as e:
        return False, str(e)

# Function to detect vehicles in the image
def detect_vehicles(image):
    results = vehicle_model(image, device='cpu')
    detections = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = round(float(box.conf[0]), 2)
            cls = int(box.cls[0])
            vehicle_class = VEHICLE_CLASS_NAMES[cls]
            if vehicle_class in ["car", "bus", "truck"] and conf > 0.5:
                detections.append({
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "detected_class": vehicle_class,  # Use detected_class
                    "confidence": conf
                })
    return detections

# Implement the gRPC server
class VehicleDetectionService(vehicle_detection_pb2_grpc.VehicleDetectionServicer):
    def Detect(self, request, context):
        # Decode image from bytes
        nparr = np.frombuffer(request.image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Detect vehicles
        detections = detect_vehicles(img)

        # Format response
        vehicles = [
            vehicle_detection_pb2.Vehicle(
                x1=int(d['x1']),
                y1=int(d['y1']),
                x2=int(d['x2']),
                y2=int(d['y2']),
                detected_class=d['detected_class'],  # Use detected_class in response
                confidence=float(d['confidence'])
            ) for d in detections
        ]
        return vehicle_detection_pb2.VehicleResponse(vehicles=vehicles)

    # Method to handle model updates
    def UpdateModel(self, request, context):
        global vehicle_model
        model_url = request.model_url

        # Download the new model
        success, message = download_model(model_url)

        if success:
            # Reinitialize the model with the new weights
            try:
                vehicle_model = YOLO('new_vehicle_model.pt')
                return vehicle_detection_pb2.ModelResponse(success=True, message="Vehicle model updated successfully")
            except Exception as e:
                return vehicle_detection_pb2.ModelResponse(success=False, message=f"Failed to load model: {str(e)}")
        else:
            return vehicle_detection_pb2.ModelResponse(success=False, message=message)

# Run the gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    vehicle_detection_pb2_grpc.add_VehicleDetectionServicer_to_server(VehicleDetectionService(), server)
    server.add_insecure_port('[::]:50052')
    print("Vehicle Detection Server started on port 50052")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()