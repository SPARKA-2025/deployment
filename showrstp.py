import cv2
import aiohttp
import asyncio
import numpy as np
import time

# RTSP stream URL (replace with your RTSP URL)
rtsp_url = "rtsp://admin:labai%402023@10.10.118.220:554/Streaming/channels/1"
video = "Gate20mobil.mp4"
import cv2
import redis
import io
import time

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
            image_bytes = buffer.tobytes()
            r.set('live_stream', image_bytes)
    else:
        # Video has ended; restart playback
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # Break the loop with a key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
