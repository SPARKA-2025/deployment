from kafka import KafkaConsumer
import json

# Configure the consumer to connect to the Kafka service running in Docker
consumer = KafkaConsumer(
    'my_topic',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

def consume_messages():
    for message in consumer:
        print(f"Received: {message.value}")

if __name__ == "__main__":
    consume_messages()
