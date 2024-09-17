import pika
import json
from minio import Minio
from minio.error import S3Error
import paho.mqtt.client as mqtt
from io import BytesIO
import base64
import time

# MinIO Configuration
MINIO_ENDPOINT = 'minio_server:9000'
MINIO_ACCESS_KEY = '8QY33QXTFMU27CA0XPCG'
# MINIO_ACCESS_KEY = '4528D5M99EBZEVKSMV07'
MINIO_SECRET_KEY = 'BTrttKDUfCbY7WdXQh85CGt8NXfMCBhHnrxE0zaa'
# MINIO_SECRET_KEY = 'OuI3+AGtkvn0+ljspM+aVVIzA+wsM6o90TaU8vdL'
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

RABBITMQ_URL = 'amqp://remosto:remosto123@rabbitmq:5672/'

def connect_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not available, retrying in 2 seconds...")
            time.sleep(2)

# Use the function to connect

mqtt_client = mqtt.Client()
mqtt_client.connect("mqtt", 1883, 60)

# Function to handle RabbitMQ messages
def callback(ch, method, properties, body):
    data = json.loads(body)
    image_name = data['image_name']
    image_base64 = data['image']
    
    # Decode base64 image
    image_bytes = base64.b64decode(image_base64)
    print("try to save")
    
    # Create a BytesIO object for MinIO
    image_stream = BytesIO(image_bytes)
    
    try:
        # Upload image to MinIO
        minio_client.put_object(
            BUCKET_NAME,
            image_name,
            image_stream,
            length=len(image_bytes),
            content_type='image/jpg'
        )
        
        # Send MQTT message on success
        mqtt_client.publish("upload/status", json.dumps({"status": "success", "image": image_name}))
        print(f"Image {image_name} uploaded successfully")
    except Exception as e:
        # Send MQTT message on error
        mqtt_client.publish("upload/status", json.dumps({"status": "error", "message": str(e)}))
        print(f"Error uploading image {image_name}: {str(e)}")

# RabbitMQ setup
def start_consumer():
    connection = connect_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue='image_queue')
    
    channel.basic_consume(queue='image_queue', on_message_callback=callback, auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()