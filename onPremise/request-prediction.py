import cv2
import redis
import numpy as np
import requests
import time

# Initialize Redis connection
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
except redis.ConnectionError as e:
    print(f"Error: Unable to connect to Redis. Exception: {e}")

SERVER_URL = "http://localhost:80/predict"

# Initialize the time and FPS variables
prev_time = 0
fps = 0
print('Initialization successful.')

while True:
    # Retrieve image from Redis
    time_load = time.time()
    try:
        image_bytes = r.get('live_stream')
        if image_bytes is None:
            print("Warning: No image data found in Redis for key 'live_stream'.")
            continue
    except redis.RedisError as e:
        print(f"Error: Failed to retrieve image from Redis. Exception: {e}")
        break
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            print("Error: Failed to decode image.")
            continue
        # Calculate FPS
        current_time = time.time()
        elapsed_time = current_time - prev_time
        prev_time = current_time
        
        fps = 1 / elapsed_time if elapsed_time > 0 else 0
        
        # Display FPS on the image
        cv2.putText(img, f'FPS: {fps:.2f}', (1300, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # Prepare the image for the POST request (encode as JPEG)
        _, img_encoded = cv2.imencode('.jpg', img)
        if img_encoded is None:
            print("Error: Failed to encode image.")
            continue

        img = cv2.rectangle(img, (600, 500), (1100, 800), (255, 0, 255), 5)
        infer_time = time.time()

    except Exception as e:
        print(f"Error during image processing: {e}")
        break
    # Send the image to the Flask server
    try:
        response = requests.post(SERVER_URL, files={'image': img_encoded.tobytes()}, timeout=5)
        # response.raise_for_status()  # Raises HTTPError if the status is 4xx or 5xx
        # Process server response (e.g., metadata)
        data = response.json()
        print(data)
        if data and isinstance(data, list):
            print(data)
            plate = data[0].get('plate_position')
            vehicle = data[0].get('vehicle_position')
            if plate and vehicle:
                img = cv2.rectangle(img, (vehicle['x1'], vehicle['y1']), (vehicle['x2'], vehicle['y2']), (255, 255, 255), 4)
                img = cv2.rectangle(
                    img,
                    (vehicle['x1'] + plate['x1'], vehicle['y1'] + plate['y1']),
                    (vehicle['x1'] + plate['x2'], vehicle['y1'] + plate['y2']),
                    (255, 255, 255), 4
                )
                cv2.imshow('New Window', img)
        else:
            # print("Warning: No valid data received from server.")
            pass
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to the server. Exception: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error during the request: {e}")
    try:
        # Display the image
        cv2.imshow('Live Stream', img)
        # print(f"Inference time: {round(time.time() - infer_time, 2)}s, Load time: {round(infer_time - time_load, 2)}s")
        
        # Break the loop with a key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    except Exception as e:
        print(f"Error during image display: {e}")
        break

cv2.destroyAllWindows()
