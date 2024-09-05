import os
from flask import Flask, request, jsonify
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.query_api import QueryApi

app = Flask(__name__)

# InfluxDB configurations
bucket = "sparka"
org = "REMOSTO TEAM"
token = "d-4-vXmqMeaynhzXc4FNeCWfe1ZRMN6D0kgqYYd7KmbnOJvi2epBOaDU3YcOZs5flLNYf-olHXxK15LCNVapmA=="
# token = "inisalahtokennya"
url = "http://localhost:8086"
# url = 'http://host.docker.internal:8086'
# url = 'https://influxdb-648108538163.asia-southeast2.run.app/orgs/a3607e25c44b1902'

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

@app.route('/check', methods=['GET'])
def check():
    return jsonify({"message": "Server are running correctly"}), 200

@app.route('/save', methods=['POST'])
def save_data():
    data = request.json
    measurement = data.get('measurement')
    fields = data.get('fields')
    tags = data.get('tags', {})
    
    if not measurement or not fields:
        print("data error")
        return jsonify({"error": "Invalid data format"}), 400
    
    point = Point(measurement)
    
    for tag_key, tag_value in tags.items():
        point.tag(tag_key, tag_value)
        
    for field_key, field_value in fields.items():
        point.field(field_key, field_value)
    
    try:
        write_api.write(bucket=bucket, org=org, record=point)
        return jsonify({"message": "Data saved successfully"}), 200
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500
    

@app.route('/query', methods=['POST'])
def query_data():
    data = request.json
    measurement = data.get('measurement')
    start_time = data.get('start', '-1h')  # Default to last 1 hour
    stop_time = data.get('stop', 'now()')  # Default to current time

    if not measurement:
        return jsonify({"error": "Measurement parameter is required"}), 400

    try:
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
        '''
        
        result = query_api.query(org=org, query=query)
        data = []
        
        for table in result:
            for record in table.records:
                data.append({
                    "time": record.get_time(),
                    "measurement": record.get_measurement(),
                    "field": record.get_field(),
                    "value": record.get_value(),
                    "tags": record.values
                })
        
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)