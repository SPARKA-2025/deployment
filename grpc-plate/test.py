import grpc
import detection_pb2
import detection_pb2_grpc
import cv2
import time

channel = grpc.insecure_channel('localhost:50051')
stub = detection_pb2_grpc.PlateDetectionStub(channel)

def run():
    # Membaca gambar dan mengirim ke server
    now = time.time()
    image_path = "image.jpg"
    img = cv2.imread(image_path)
    _, img_encoded = cv2.imencode('.jpg', img)
    image_data = img_encoded.tobytes()

    # Membuat channel gRPC dan stub
    # Membuat request
    for i in range(1):
        response = stub.Detect(detection_pb2.ImageRequest(image_data=image_data))
        print(response.plates)

        # Menampilkan hasil deteksi
        # for plate in response.plates:
        #     print(f"Detected plate at ({plate.x1}, {plate.y1}, {plate.x2}, {plate.y2}) with confidence {plate.confidence}")
    print(time.time()-now)

if __name__ == "__main__":
    run()
