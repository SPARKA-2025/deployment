import psutil
import requests
import json
import time
import os

# Function to get system usage statistics
def get_system_usage():
    cpu_percentages = psutil.cpu_percent(interval=1, percpu=True)  # CPU usage per core
    cpu_freq = psutil.cpu_freq()  # Get CPU frequency
    virtual_mem = psutil.virtual_memory()  # Get virtual memory details
    swap_mem = psutil.swap_memory()  # Get swap memory details
    
    # Creating a flat structure with key-value pairs
    usage_data = {
        # CPU usage per core
        **{f"cpu_{i+1}": cpu_percentages[i] for i in range(len(cpu_percentages))},
        
        # CPU frequency details
        "cpu_freq_current": cpu_freq.current,
        "cpu_freq_min": cpu_freq.min,
        "cpu_freq_max": cpu_freq.max,
        
        # CPU core counts
        "cpu_logical_cores": psutil.cpu_count(logical=True),
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        
        # RAM details
        "ram_total": virtual_mem.total,
        "ram_available": virtual_mem.available,
        "ram_used": virtual_mem.used,
        "ram_free": virtual_mem.free,
        "ram_percent": virtual_mem.percent,
        
        # Swap memory details
        "swap_total": swap_mem.total,
        "swap_used": swap_mem.used,
        "swap_free": swap_mem.free,
        "swap_percent": swap_mem.percent
    }
    
    return usage_data

# Function to send data to the server
def send_to_server(data, server_url):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(server_url, data=json.dumps(data), headers=headers)
    # print(response.json())
    return response.status_code, response

# Server URL (replace with your server's URL)
server_url = "http://influxdb_gateway:5000/save"

# Monitor and send system usage data every 10 seconds
try:
    while True:
        usage_data = get_system_usage()
        payload = {
            "measurement": "resource_usage",
            "fields": usage_data,
            "tags": {
                "location": "cloud_server"
            }
        }
        print(payload)
        status_code, response = send_to_server(payload, server_url)
        print(f"Server response status code: {status_code}")
        print(f"response {response}")
        time.sleep(1)
except KeyboardInterrupt:
    print("Monitoring stopped.")