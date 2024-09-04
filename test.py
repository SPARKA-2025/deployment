import requests
import cv2

# Server URL (Adjust if needed)
SERVER_URL = "http://host.docker.internal:5001/predict"

# Path to the test image
image_path = "image.jpg"

def test_flask_server(image_path):
    # Read the image
    image = cv2.imread(image_path)
    _, img_encoded = cv2.imencode('.jpg', image)
    
    # Prepare payload
    files = {'image': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')}
    
    # Send POST request to Flask server
    response = requests.post(SERVER_URL, files=files)
    
    if response.status_code == 200:
        print("Response from server:")
        print(response.json())  # Display the JSON response from the server
    else:
        print(f"Failed to get response. Status code: {response.status_code}")
        print("Response content:", response.content)

if __name__ == "__main__":
    # while True:
    test_flask_server(image_path)
