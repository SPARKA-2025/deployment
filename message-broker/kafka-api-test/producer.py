from kafka import KafkaProducer
import json
import time

# Configure the producer to connect to the Kafka service running in Docker
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def produce_messages():
    for i in range(10):
        data = {'number': i}
        producer.send('my_topic', value=data)
        print(f"Sent: {data}")
        time.sleep(1)  # Wait a second between messages

    producer.flush()  # Ensure all messages are sent before closing

if __name__ == "__main__":
    produce_messages()
