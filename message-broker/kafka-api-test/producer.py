from kafka import KafkaConsumer
import cv2
import numpy as np

# Configure the Kafka consumer
consumer = KafkaConsumer(
    'image_topic',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

def consume_image():
    for message in consumer:
        # Convert byte data back into a NumPy array and decode the image
        image_bytes = message.value
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Display the image
        cv2.imshow("Received Image", image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    consume_image()
