import requests
from random import randint
import time
import random
import time

# URL to which the request will be sent
url = 'http://127.0.0.1:5000/save'

# JSON payload to be sent with the request

# Sending the POST request with JSON data
while True:
    # Example of prediction_metadata with random values
    prediction_metadata = {
        "plate_position": {
            "x1": random.uniform(0, 100),
            "x2": random.uniform(0, 100),
            "y1": random.uniform(0, 100),
            "y2": random.uniform(0, 100),
        },
        "vehicle_position": {
            "x1": random.uniform(0, 100),
            "x2": random.uniform(0, 100),
            "y1": random.uniform(0, 100),
            "y2": random.uniform(0, 100),
        },
        "plate_number": f"ABC{random.randint(1000, 9999)}",
        "vehicle_class": random.choice(["sedan", "SUV", "truck", "motorbike"]),
    }

    filename = f"image_random.jpg"
    time_now = int(time.time())

    # Construct the request data
    request_data = {
        "measurement": "plate_detection",
        "fields": {
            "plate_position_x": (prediction_metadata['plate_position']['x1'] + prediction_metadata['plate_position']['x2']) / 2,
            "plate_position_y": (prediction_metadata['plate_position']['y1'] + prediction_metadata['plate_position']['y2']) / 2,
            "vehicle_position_x": (prediction_metadata['vehicle_position']['x1'] + prediction_metadata['vehicle_position']['x2']) / 2,
            "vehicle_position_y": (prediction_metadata['vehicle_position']['y1'] + prediction_metadata['vehicle_position']['y2']) / 2,
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

    print(request_data)

    # Headers (optional)
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.post(url, json=request_data, headers=headers)

    # Printing the response
    print(response.status_code)
    print(response.json())  # Assuming the response is in JSON format
    time.sleep(0.1)
