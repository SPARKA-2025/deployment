import grpc
import detection_pb2
import detection_pb2_grpc
import cv2
import time
import numpy as np

channel = grpc.insecure_channel('localhost:50051')
stub = detection_pb2_grpc.PlateDetectionStub(channel)

def run():
    now = time.time()
    image_path = "image.jpg"
    img = cv2.imread(image_path)
    _, img_encoded = cv2.imencode('.jpg', img)
    image_data = img_encoded.tobytes()

    for i in range(1):
        response = stub.Detect(detection_pb2.ImageRequest(image_data=image_data))
        metadata = response.plates[0]
        arr = np.vstack((np.empty((0, 5)), [metadata.x1,metadata.y1,metadata.x2,metadata.y2,metadata.confidence]))
        print(arr)
        print(type(arr))

    print(time.time()-now)

if __name__ == "__main__":
    run()
