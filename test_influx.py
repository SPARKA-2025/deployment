import requests
from random import randint
import time

# URL to which the request will be sent
url = 'http://127.0.0.1:5000/save'

# JSON payload to be sent with the request

# Sending the POST request with JSON data
while True:
    payload = {
        "measurement": "temperature",
        "fields": {
            "value": randint(0, 30)/3
        },
        "tags": {"location": "office"}
    }


    # Headers (optional)
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.post(url, json=payload, headers=headers)

    # Printing the response
    print(response.status_code)
    print(response.json())  # Assuming the response is in JSON format
    time.sleep(0.1)
