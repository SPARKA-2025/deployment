from ultralytics import YOLO
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='en', det=True, rec=True, use_angle_cls=False, det_db_unclip_ratio=1.2, det_db_box_thresh=0.1, drop_score=0.6, max_text_length=9)
plate_model = YOLO("models/updated_model3.pt")
vehicle_model = YOLO("models/yolov8n.pt")

print("environtment are correct and ready to run")