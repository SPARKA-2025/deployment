import requests

# Define the server URL
server_url = "http://127.0.0.1:5002"

# Paths to test image files
upload_image_path = "asd.jpg"  # Replace with the path to your test image
download_image_name = "image.jpg"  # Replace with the path to save the downloaded image

import time
print()

def upload_image(image_path):
    url = f"{server_url}/upload"
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}
        response = requests.post(url, files=files)
        
    if response.status_code == 200:
        print("Upload successful:", response.json())
    else:
        print("Upload failed:", response.json())

def download_image(image_name, save_path):
    url = f"{server_url}/download/{image_name}"
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download successful, saved as:", save_path)
    else:
        print("Download failed:", response.json())

if __name__ == "__main__":
    # Step 1: Upload the image to the server
    print("Uploading image...")
    upload_image(upload_image_path)
    
    # Step 2: Download the image from the server
    print("Downloading image...")
    image_name = upload_image_path.split("/")[-1]  # Assuming the image name is the same as the uploaded image
    download_image(image_name, download_image_name)
