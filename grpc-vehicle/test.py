import grpc
import vehicle_detection_pb2
import vehicle_detection_pb2_grpc
import cv2

channel = grpc.insecure_channel('localhost:50052')
stub = vehicle_detection_pb2_grpc.VehicleDetectionStub(channel)

def detect_vehicles(image_path):
    # Read the image
    img = cv2.imread(image_path)
    _, img_encoded = cv2.imencode('.jpg', img)
    image_data = img_encoded.tobytes()

    response = stub.Detect(vehicle_detection_pb2.ImageRequest(image_data=image_data))

    # Display results
    detected = []
    for vehicle in response.vehicles:
        detected.append({
            'x1': vehicle.x1,
            'y1': vehicle.y1,
            'x2': vehicle.x2,
            'y2': vehicle.y2,
            'class': vehicle.detected_class,
            'confidence': vehicle.confidence,
        })

    # print(f"Detected {vehicle.detected_class} at ({vehicle.x1}, {vehicle.y1}, {vehicle.x2}, {vehicle.y2}) with confidence {vehicle.confidence}")
    print(detected)
if __name__ == "__main__":
    detect_vehicles('image.jpg')
