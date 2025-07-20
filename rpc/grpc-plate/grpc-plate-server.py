import grpc
import detection_pb2
import detection_pb2_grpc
import cv2
import numpy as np
import requests
from ultralytics import YOLO
from concurrent import futures

# Load YOLO model
# Initialize models
plate_model = YOLO("model/updated_model3.pt")
# vehicle_model = YOLO("model/yolov8n.pt")
  
# Constants
CLASS_NAMES = ["plat"]
# VEHICLE_CLASS_NAMES = vehicle_model.names
PROCESSED_IDS = {}


# Function to download the model
def download_model(model_url, save_path='new_model.pt'):
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

# Function to detect plates
def detect_plate(vehicle_img):
    plate_results = plate_model(vehicle_img, device='cpu', stream=True)
    plate_detections = np.empty((0, 5))
    for r in plate_results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            conf = round(float(box.conf[0]), 2)
            if CLASS_NAMES[int(box.cls[0])] == "plat" and conf > 0.5:
                plate_detections = np.vstack((plate_detections, [x1, y1, x2, y2, conf]))
    return plate_detections

# gRPC server implementation
class PlateDetectionService(detection_pb2_grpc.PlateDetectionServicer):
    def Detect(self, request, context):
        # Decode image from bytes
        nparr = np.frombuffer(request.image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Detect plates
        detections = detect_plate(img)
        
        # Prepare response
        plates = [
            detection_pb2.Plate(
                x1=int(detection[0]),
                y1=int(detection[1]),
                x2=int(detection[2]),
                y2=int(detection[3]),
                confidence=float(detection[4])
            ) for detection in detections
        ]
        return detection_pb2.PlateResponse(plates=plates)

    # Method to handle model updates
    def UpdateModel(self, request, context):
        global plate_model
        model_url = request.model_url

        # Download the new model
        success, message = download_model(model_url)

        if success:
            # Reinitialize the model with the new weights
            try:
                plate_model = YOLO('new_model.pt')  # Use the downloaded model
                return detection_pb2.ModelResponse(success=True, message="Model updated successfully")
            except Exception as e:
                return detection_pb2.ModelResponse(success=False, message=f"Failed to load model: {str(e)}")
        else:
            return detection_pb2.ModelResponse(success=False, message=message)

# Run the gRPC server
def serve():
    import os
    port = os.getenv('GRPC_PORT', '50053')  # Use environment variable or default to 50053
    print(f"Environment GRPC_PORT: {port}")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    detection_pb2_grpc.add_PlateDetectionServicer_to_server(PlateDetectionService(), server)
    server.add_insecure_port(f'[::]:{port}')
    print(f"Server started on port {port}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()