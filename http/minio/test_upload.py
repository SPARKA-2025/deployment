import requests
import os

def test_upload_image():
    """Test uploading an image to MinIO server"""
    # Check if test image exists
    test_image_path = 'image.jpg'
    if not os.path.exists(test_image_path):
        print(f"Test image {test_image_path} not found")
        return
    
    # Upload image to MinIO server
    minio_url = 'http://localhost:5002/upload'
    
    try:
        with open(test_image_path, 'rb') as image_file:
            files = {'image': ('test_image.jpg', image_file, 'image/jpeg')}
            response = requests.post(minio_url, files=files)
            
        if response.status_code == 200:
            print('✅ Image uploaded successfully to MinIO!')
            print('Response:', response.json())
            
            # Test download
            download_url = 'http://localhost:5002/download/test_image.jpg'
            download_response = requests.get(download_url)
            
            if download_response.status_code == 200:
                print('✅ Image download test successful!')
                print(f'Downloaded image size: {len(download_response.content)} bytes')
            else:
                print('❌ Image download test failed:', download_response.text)
        else:
            print('❌ Image upload failed:', response.text)
            
    except Exception as e:
        print(f'❌ Error testing upload: {str(e)}')

if __name__ == '__main__':
    test_upload_image()