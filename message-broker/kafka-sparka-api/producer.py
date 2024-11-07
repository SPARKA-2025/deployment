from kafka import KafkaProducer
import cv2
import numpy as np

# Configure the Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092'
)

def send_image(image_path):
    # Read and encode the image
    image = cv2.imread(image_path)
    _, buffer = cv2.imencode('.jpg', image)
    image_bytes = buffer.tobytes()

    # Send the image bytes to Kafka
    producer.send('image_topic', value=image_bytes)
    producer.flush()
    print("Image sent to Kafka.")

if __name__ == "__main__":
    send_image("image.jpg")
