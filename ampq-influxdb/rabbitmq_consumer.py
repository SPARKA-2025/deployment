import pika
import json
from influxdb_client import InfluxDBClient, Point
import os
import time

# InfluxDB configuration
bucket = "sparka"
org = "RemostoTeam"
token = "n6HCiO-f5dz1vRGzeT64eid9As5FvY_Wn0sR_bB9bXbPd1ZEeiC4pwJ4FyexRQD9QqT-NS3Bz7ItppVg0nks0Q=="
url = "http://influxdb:8086"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api()

RABBITMQ_URL = 'amqp://guest:guest@rabbitmq:5672/'

def connect_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not available, retrying in 2 seconds...")
            time.sleep(2)

def callback(ch, method, properties, body):
    data = json.loads(body)
    
    measurement = data.get('measurement')
    fields = data.get('fields')
    tags = data.get('tags', {})
    
    if not measurement or not fields:
        print("data error")
        return
    
    point = Point(measurement)
    
    for tag_key, tag_value in tags.items():
        point.tag(tag_key, tag_value)
        
    for field_key, field_value in fields.items():
        point.field(field_key, field_value)
    
    try:
        write_api.write(bucket=bucket, org=org, record=point)
        print(" [x] Data saved successfully")
    except Exception as e:
        print(f" [x] Error: {str(e)}")

def main():
    connection =connect_rabbitmq()
    channel = connection.channel()
    
    # Declare the queue
    channel.queue_declare(queue='data_queue')
    
    # Set up subscription
    channel.basic_consume(queue='data_queue',
                          on_message_callback=callback,
                          auto_ack=True)
    
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    main()
