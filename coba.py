import cv2
import redis
import numpy as np
import requests
import time

# Initialize Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)
SERVER_URL = "http://127.0.0.1:5001/predict"

# Initialize the time and FPS variables
prev_time = 0
fps = 0

while True:
    # Retrieve image from Redis
    image_bytes = r.get('live_stream')
    
    if image_bytes:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Calculate FPS
        current_time = time.time()
        elapsed_time = current_time - prev_time
        prev_time = current_time
        
        fps = 1 / elapsed_time if elapsed_time > 0 else 0
        
        # Display FPS on the image
        cv2.putText(img, f'FPS: {fps:.2f}', (1300, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # Prepare the image for the POST request (encode as JPEG)
        _, img_encoded = cv2.imencode('.jpg', img)

        # Send the image to the Flask server
        try:
            response = requests.post(SERVER_URL, files={'image': img_encoded.tobytes()})
            if response.status_code == 200:
                # Process server response (e.g., metadata)
                print(response.json())
            else:
                print("Error: Server responded with status code", response.status_code)
        except requests.exceptions.RequestException as e:
            print(f"Error: Could not connect to server. Exception: {e}")
        
        # Display the image
        cv2.imshow('Live Stream', img)
        
        # Break the loop with a key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
