from flask import Flask, request, jsonify
import jwt
import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Secret key for encoding and decoding JWT tokens
SECRET_KEY = 'my-secret-key-that-long-and-secure-hehe'

def generate_jwt_token(user_id):
    # Define the token's payload
    payload = {
        'sub': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    # Encode the payload to create the JWT token
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    # Convert the token from bytes to string if necessary
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    return token

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data['username'] == 'remosto' and data['password'] == 'remosto123': 
        token = generate_jwt_token(user_id="1234")
        return jsonify({"token": token}), 200
    return jsonify({"message": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003)
