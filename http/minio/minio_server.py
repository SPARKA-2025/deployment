from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from io import BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Local storage configuration (fallback when MinIO is not available)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image = request.files['image']
    if image.filename == '':
        return jsonify({'error': 'No image file selected'}), 400
    
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            image.save(file_path)
            return jsonify({'message': 'Image uploaded successfully', 'filename': filename}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<image_name>', methods=['GET'])
def download_image(image_name):
    try:
        # Secure the filename to prevent directory traversal
        safe_filename = secure_filename(image_name)
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        if os.path.exists(file_path):
            # Determine content type based on file extension
            file_ext = safe_filename.rsplit('.', 1)[1].lower() if '.' in safe_filename else 'jpg'
            content_type = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg', 
                'png': 'image/png',
                'gif': 'image/gif'
            }.get(file_ext, 'image/jpeg')
            
            return send_file(
                file_path,
                mimetype=content_type,
                as_attachment=False,  # Display in browser
                download_name=safe_filename
            )
        else:
            return jsonify({'error': f'File not found: {safe_filename}'}), 404
    except Exception as e:
        return jsonify({'error': f'Error accessing file: {str(e)}'}), 500
    
@app.route('/delete/<image_name>', methods=['DELETE'])
def delete_image(image_name):
    try:
        # Secure the filename to prevent directory traversal
        safe_filename = secure_filename(image_name)
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': f'{safe_filename} has been deleted successfully.'}), 200
        else:
            return jsonify({'error': f'File not found: {safe_filename}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
