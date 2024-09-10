import cv2
import numpy as np
import cv2
import redis

# RTSP stream URL (replace with your RTSP URL)
rtsp_url = "rtsp://admin:labai%402023@10.10.118.220:554/Streaming/channels/1"
video = "D:/Project/plate-number-api/sparka-server-api/video/Gate20mobil.mp4"

# Initialize Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)

# Open video capture
cap = cv2.VideoCapture(video)  # Change 0 to your video source

while True:
    # Capture a frame
    ret, frame = cap.read()
    if ret:
        # Encode image to JPEG format
        is_success, buffer = cv2.imencode(".jpg", frame)
        if is_success:
            # Convert buffer to bytes and save to Redis
            try:
                image_bytes = buffer.tobytes()
                coba = r.set('live_stream', image_bytes)
            except:
                print('error')

    else:
        # Video has ended; restart playback
        print('error')
    # Break the loop with a key press

# Release resources
cap.release()
cv2.destroyAllWindows()
