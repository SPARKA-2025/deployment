import grpc
import plate_text_extraction_pb2
import plate_text_extraction_pb2_grpc
import cv2
import numpy as np
import os
from paddleocr import PaddleOCR
from concurrent import futures

# Initialize the OCR model
ocr = PaddleOCR(lang='en', det=True, rec=True, use_angle_cls=False, det_db_unclip_ratio=1.2, det_db_box_thresh=0.1, drop_score=0.6, max_text_length=9)

# Function to extract plate text
def extract_plate_text(image):
    result = ocr.ocr(image, cls=True)
    if result is None or len(result) == 0 or result[0] is None:
        return "No text detected"
    try:
        return ''.join([res[1][0] for res in result[0]])
    except Exception as e:
        print(f"Error extracting text: {e}")
        return "Error during text extraction"

# Implement the gRPC server
class PlateTextExtractionService(plate_text_extraction_pb2_grpc.PlateTextExtractionServicer):
    def Extract(self, request, context):
        print(f"Received OCR request with image data size: {len(request.image_data)} bytes")
        # Decode the image from bytes
        nparr = np.frombuffer(request.image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Extract text from the image
        text = extract_plate_text(img)
        print(f"Extracted text: '{text}'")

        # Return the extracted text
        return plate_text_extraction_pb2.TextResponse(text=text)

# Run the gRPC server
def serve():
    port = os.getenv('GRPC_PORT', '50052')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    plate_text_extraction_pb2_grpc.add_PlateTextExtractionServicer_to_server(PlateTextExtractionService(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Plate Text Extraction Server started and listening on port {port}")
    print("Server is ready to accept requests...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
