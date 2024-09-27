import pika
import cv2
import json
import base64

def send_image(image_path, image_name, rabbitmq_url):
    # Read the image
    image = cv2.imread(image_path)
    _, image_encoded = cv2.imencode('.jpg', image)
    
    # Encode the image bytes in base64
    image_base64 = base64.b64encode(image_encoded.tobytes()).decode('utf-8')
    
    # Establish connection with RabbitMQ
    connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    channel = connection.channel()
    
    # Declare the queue
    channel.queue_declare(queue='image_queue')
    
    # Send the message (image + metadata)
    message = {
        'image_name': image_name,
        'image': image_base64
    }
    channel.basic_publish(exchange='', routing_key='image_queue', body=json.dumps(message))
    
    print(f" [x] Sent image {image_name}")
    connection.close()

# Usage
send_image('image.jpg', 'image_name.jpg', 'amqp://remosto:remosto123@localhost:5672/')
