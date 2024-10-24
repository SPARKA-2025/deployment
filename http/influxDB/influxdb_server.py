from flask import Flask, request, jsonify
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import jwt
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# InfluxDB configurations
bucket = "sparka"
org = "RemostoTeam"
token = "n6HCiO-f5dz1vRGzeT64eid9As5FvY_Wn0sR_bB9bXbPd1ZEeiC4pwJ4FyexRQD9QqT-NS3Bz7ItppVg0nks0Q=="
url = "http://influxdb:8086"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

SECRET_KEY = 'my-secret-key-that-long-and-secure-hehe'

def token_required(f):
    def decorator(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        try:
            token = token.split(" ")[1]
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    
    return decorator


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

# @token_required
@app.route('/query', methods=['POST'])
def query_data():
    data = request.json
    measurement = data.get('measurement')
    start_time = data.get('start', '-1h')  
    stop_time = data.get('stop', 'now()')

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
        print(e)
        return jsonify({"error": str(e)}), 500

@token_required
@app.route('/delete/all', methods=['DELETE'])
def delete_all_data():
    measurement = request.json.get('measurement')
    if not measurement:
        return jsonify({"error": "Measurement parameter is required"}), 400

    try:
        delete_api = client.delete_api()
        delete_api.delete(start="1970-01-01T00:00:00Z", stop="now()", predicate=f'_measurement="{measurement}"', bucket=bucket, org=org)
        return jsonify({"message": f"All data in measurement '{measurement}' deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@token_required
@app.route('/delete/range', methods=['DELETE'])
def delete_range_data():
    data = request.json
    measurement = data.get('measurement')
    start_time = data.get('start')
    stop_time = data.get('stop')

    if not measurement or not start_time or not stop_time:
        return jsonify({"error": "Measurement, start, and stop parameters are required"}), 400

    try:
        delete_api = client.delete_api()
        delete_api.delete(start=start_time, stop=stop_time, predicate=f'_measurement="{measurement}"', bucket=bucket, org=org)
        return jsonify({"message": f"Data in measurement '{measurement}' from {start_time} to {stop_time} deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)