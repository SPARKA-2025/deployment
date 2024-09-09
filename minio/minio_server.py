from flask import Flask, request, jsonify, send_file
from minio import Minio
from minio.error import S3Error
from flask_cors import CORS
import os
from io import BytesIO

app = Flask(__name__)
CORS(app)

# MinIO Configuration
MINIO_ENDPOINT = 'minio:9000'
# MINIO_ACCESS_KEY = '8QY33QXTFMU27CA0XPCG'
MINIO_ACCESS_KEY = '4528D5M99EBZEVKSMV07'
# MINIO_SECRET_KEY = 'BTrttKDUfCbY7WdXQh85CGt8NXfMCBhHnrxE0zaa'
MINIO_SECRET_KEY = 'OuI3+AGtkvn0+ljspM+aVVIzA+wsM6o90TaU8vdL'
BUCKET_NAME = 'sparka-image'

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set to True if using HTTPS
)

# Ensure the bucket exists
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image = request.files['image']
    image_name = image.filename
    
    # Save image to MinIO
    try:
        minio_client.put_object(
            BUCKET_NAME, 
            image_name, 
            image.stream, 
            length=-1, 
            part_size=10*1024*1024,  # 10 MB part size
            content_type=image.content_type
        )
        return jsonify({'message': 'Image uploaded successfully'}), 200
    except S3Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<image_name>', methods=['GET'])
def download_image(image_name):
    try:
        response = minio_client.get_object(BUCKET_NAME, image_name)
        
        # Get the content type from the object headers
        stat = minio_client.stat_object(BUCKET_NAME, image_name)
        content_type = stat.content_type
        
        return send_file(
            BytesIO(response.read()), 
            mimetype=content_type, 
            as_attachment=True, 
            download_name=image_name
        )
    except S3Error as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
