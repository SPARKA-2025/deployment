import pika
import json

RABBITMQ_URL = 'amqp://guest:guest@localhost:5672/'

def send_to_rabbitmq(data, queue_name='data_queue'):
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    
    # Declare the queue
    channel.queue_declare(queue=queue_name)
    
    # Send data to the queue
    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=json.dumps(data),
                          properties=pika.BasicProperties(
                              content_type='application/json',
                          ))
    
    print(" [x] Sent data to RabbitMQ")
    connection.close()

# Example usage
data = {
    "measurement": "temperature",
    "fields": {"value": 23.5},
    "tags": {"location": "office"}
}
send_to_rabbitmq(data)
