import numpy as np
from ultralytics import YOLO
import cv2
import cvzone
import math
from paddleocr import PaddleOCR
from sort import *
import os
import datetime
import requests

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def preprocess_image(image):
    h, w, _ = image.shape
    resized_image = cv2.resize(image, (w * 2, h * 2))
    cleaned_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    cleaned_image = cv2.GaussianBlur(cleaned_image, (5, 5), 0)
    return cleaned_image

def resize_region(image, scale=2):
    h, w, _ = image.shape
    resized_image = cv2.resize(image, (int(w * scale), int(h * scale)))
    return resized_image

def is_valid_plate(plate_text):
    return len(plate_text) >= 6 and plate_text[0].isalpha() and plate_text[-1].isalpha()

def post_to_backend(capture_time, vehicle, plat_nomor, location, image1):
    backend_url = 'https://x.run.app/api/admin/log-kendaraan'
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vc3BhcmthLWJlLWZnenVzd2htMnEtZXQuYS5ydW4uYXBwL2FwaS9sb2dpbi1hZG1pbiIsImlhdCI6MTcyMDc2MDAzOSwiZXhwIjoyMDM2MTIwMDM5LCJuYmYiOjE3MjA3NjAwMzksImp0aSI6Im82ZGw0TTk2NHhBZWRteUUiLCJzdWIiOiIyIiwicHJ2IjoiZGY4ODNkYjk3YmQwNWVmOGZmODUwODJkNjg2YzQ1ZTgzMmU1OTNhOSJ9.Lk2dCD7crX6Wgybsq8QeI_foCV7p63oNZw2DSqU5XME"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        "capture_time": capture_time,
        "vehicle": vehicle,
        "plat_nomor": plat_nomor,
        "location": location    }
    with open(image1, 'rb') as image_file:
        files = {
            'image': image_file
        }
        response = requests.post(backend_url, headers=headers, data=data, files=files)

    if response.status_code == 200:
        print(f'Data kendaraan {plat_nomor} berhasil ditambahkan ke BE!')
    else:
        print(f'Debug data plat {plat_nomor} ke BE:', response.text)

def update_parking_slot(plat_nomor):
    backend_url = 'https://sparka-be-evfpthsuvq-et.a.run.app/api/admin/parkir/ubah-slot-ke-kosong'
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vc3BhcmthLWJlLWZnenVzd2htMnEtZXQuYS5ydW4uYXBwL2FwaS9sb2dpbi1hZG1pbiIsImlhdCI6MTcyMDc2MDAzOSwiZXhwIjoyMDM2MTIwMDM5LCJuYmYiOjE3MjA3NjAwMzksImp0aSI6Im82ZGw0TTk2NHhBZWRteUUiLCJzdWIiOiIyIiwicHJ2IjoiZGY4ODNkYjk3YmQwNWVmOGZmODUwODJkNjg2YzQ1ZTgzMmU1OTNhOSJ9.Lk2dCD7crX6Wgybsq8QeI_foCV7p63oNZw2DSqU5XME"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        "plat_nomor": plat_nomor
    }
    response = requests.post(backend_url, headers=headers, json=data)

    if response.status_code == 200:
        print(f'Slot parkir untuk plat nomor {plat_nomor} berhasil diubah ke Kosong!')
    elif response.status_code == 400:
        print(f'Slot parkir untuk plat nomor {plat_nomor} sudah kosong.')
    else:
        print(f'Gagal mengubah status slot parkir untuk plat nomor {plat_nomor}:', response.text)

# Initialize PaddleOCR

ocr = PaddleOCR(lang='en', 
                det=True, 
                rec=True, 
                use_angle_cls=False, 
                det_db_unclip_ratio=1.2, 
                det_db_box_thresh=0.1, 
                drop_score=0.6, 
                max_text_length=9)
cap = cv2.VideoCapture("Gate20mobil.mp4")
plate_model = YOLO("updated_model3.pt")  # Model untuk mendeteksi plat nomor
vehicle_model = YOLO("yolov8n.pt")  # YOLOv8 model COCO
lokasi = "Musrek"
save_dir = "saved_images"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

classNames = ["plat"]
vehicle_class_names = vehicle_model.names

tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)
processed_ids = {}
limits = [520, 325, 520, 673]  # Adjust as needed
current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.resize(img, (1080, 720))

    # Deteksi kendaraan
    vehicle_results = vehicle_model(img)
    vehicle_detections = np.empty((0, 5))

    for r in vehicle_results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            w, h = x2 - x1, y2 - y1
            conf = math.ceil((box.conf[0] * 100)) / 100
            cls = int(box.cls[0])
            currentClass1 = vehicle_class_names[cls]

            # Mendeteksi kendaraan
            if currentClass1 in ["car", "bus", "truck"] and conf > 0.5:
                currentArray = np.array([x1, y1, x2, y2, conf])
                vehicle_detections = np.vstack((vehicle_detections, currentArray))
                cvzone.cornerRect(img, (x1, y1, w, h), l=9, rt=2, colorR=(0, 255, 0))
                cvzone.putTextRect(img, f'{currentClass1} {conf}', (max(0, x1), max(35, y1)), scale=2, thickness=3, offset=0)

    # Deteksi plat nomor di dalam bounding box kendaraan
    for vehicle in vehicle_detections:
        vx1, vy1, vx2, vy2, vconf = vehicle
        vehicle_img = img[int(vy1):int(vy2), int(vx1):int(vx2)]

        plate_results = plate_model(vehicle_img, stream=True)
        plate_detections = np.empty((0, 5))

        for r in plate_results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1) + vx1 - 10, int(y1) + vy1, int(x2) + vx1 + 10, int(y2) + vy1  # Adjust to original image coordinates with margin
                x1, y1 = max(0, x1), max(0, y1)  # Ensure coordinates are within bounds
                x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)
                w, h = x2 - x1, y2 - y1
                conf = math.ceil((box.conf[0] * 100)) / 100
                cls = int(box.cls[0])
                currentClass = classNames[cls]

                if currentClass == "plat" and conf > 0.5:
                    currentArray = np.array([x1, y1, x2, y2, conf])
                    plate_detections = np.vstack((plate_detections, currentArray))

        resultsTracker = tracker.update(plate_detections)

        for result in resultsTracker:
            x1, y1, x2, y2, id = result
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            x11, y11, x22, y22 = int(x1)-10, int(y1), int(x2)-10, int(y2)
            w, h = x2 - x1, y2 - y1
            w11, h11 = x22 - x11, y22 - y11
            cx, cy = x1 + w // 2, y1 + h // 2

            region = img[y1:y1 + h, x1:x1 + w]
            region2 = img[y11:y11 + h11, x11:x11 + w11]

            if id not in processed_ids:
                if limits[0] - 15 < cx < limits[2] + 15 and limits[1] - 15 < cy < limits[3] + 15:
                    processed_ids[id] = True
                    cleaned_image = preprocess_image(region)
                    cv2.imshow("Image2", cleaned_image)

                    result = ocr.ocr(cleaned_image, cls=True)
                    if result and len(result) > 0 and result[0]:
                        text = ''.join([res[1][0] for res in result[0]])
                        if not is_valid_plate(text):
                            cleaned_image = region2
                            result = ocr.ocr(cleaned_image, cls=True)
                            if result and len(result) > 0 and result[0]:
                                text = ''.join([res[1][0] for res in result[0]])
                        if not is_valid_plate(text):
                            resized_region = resize_region(region)
                            cleaned_image = preprocess_image(resized_region)
                            result = ocr.ocr(cleaned_image, cls=True)
                            if result and len(result) > 0 and result[0]:
                                text = ''.join([res[1][0] for res in result[0]])
                        if not is_valid_plate(text):
                            result = ocr.ocr(region, cls=True)
                            if result and len(result) > 0 and result[0]:
                                text = ''.join([res[1][0] for res in result[0]])
                        
                        cvzone.putTextRect(img, f'{text}', (max(0, x1), max(35, y1)), scale=2, thickness=3, offset=0)

                        # Identify closest vehicle and save image
                        closest_vehicle_distance = float('inf')
                        closest_vehicle_img = None

                        for vehicle in vehicle_detections:
                            vx1, vy1, vx2, vy2, vconf = vehicle
                            vcx, vcy = (vx1 + vx2) // 2, (vy1 + vy2) // 2
                            distance = math.sqrt((cx - vcx) ** 2 + (cy - vcy) ** 2)
                            if distance < closest_vehicle_distance:
                                closest_vehicle_distance = distance
                                closest_vehicle_img = img[int(vy1):int(vy2), int(vx1):int(vx2)]

                        if closest_vehicle_img is not None:
                            vehicle_filename = f"{text}.jpg"
                            vehicle_filepath = os.path.join(save_dir, vehicle_filename)
                            image1 = vehicle_filepath
                            cv2.imwrite(vehicle_filepath, closest_vehicle_img)
                            print(f"Tanggal: {current_datetime}")
                            print(f"Nomor kendaraan: {text}")
                            print(f"Lokasi: {lokasi}")
                            print(f"Kendaraan: {currentClass1}")
                            print(f"Saved closest vehicle image: {vehicle_filepath}")
                            # post_to_backend(current_datetime, currentClass1, text, lokasi, image1)

                            # Update parking slot status to empty
                            # update_parking_slot(text)
                    else:
                        print("Plat nomor tidak terdeteksi")

            cvzone.cornerRect(img, (x1, y1, w, h), l=9, rt=2, colorR=(255, 0, 255))

    # Tambahkan tanggal dan waktu di pojok kanan atas
    cv2.putText(img, current_datetime, (img.shape[1] - 300, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Gambar batas deteksi
    cv2.line(img, (limits[0], limits[1]), (limits[2], limits[3]), (0, 0, 255), 5)
    cv2.imshow("Image", img)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
