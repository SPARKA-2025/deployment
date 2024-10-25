from flask import Flask, request, jsonify
import jwt
import datetime
from flask_cors import CORS
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import os

app = Flask(__name__)
CORS(app)
SECRET_KEY = 'my-secret-key-that-long-and-secure-hehe'
OTLP_ENDPOINT = os.getenv('OTLP_ENDPOINT', 'http://jaeger:4317')

# Set up tracing resources and tracer provider
resource = Resource(attributes={"service.name": "flask_app"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer_provider().get_tracer("flask_app_tracer")

# Set up the OTLP Exporter
otlp_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# Instrument Flask with OpenTelemetry
FlaskInstrumentor().instrument_app(app)

def generate_jwt_token(user_id):
    with tracer.start_as_current_span("auth_generate_token"):
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
    with tracer.start_as_current_span("auth_login"):
        data = request.json
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"message": "Username and password are required"}), 400

        if data['username'] == 'remosto' and data['password'] == 'remosto123': 
            token = generate_jwt_token(user_id="1234")
            return jsonify({"token": token}), 200
        return jsonify({"message": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003)