import grpc
import plate_text_extraction_pb2
import plate_text_extraction_pb2_grpc
import cv2

def extract_plate_text(image_path):
    # Read the image
    img = cv2.imread(image_path)
    _, img_encoded = cv2.imencode('.jpg', img)
    image_data = img_encoded.tobytes()

    # Create a gRPC channel and stub
    channel = grpc.insecure_channel('localhost:50053')
    stub = plate_text_extraction_pb2_grpc.PlateTextExtractionStub(channel)

    # Send the image and get the response
    response = stub.Extract(plate_text_extraction_pb2.ImageRequest(image_data=image_data))

    # Print the extracted text
    print(f"Extracted text: {response.text}")

if __name__ == "__main__":
    extract_plate_text('image.jpg')
