import redis
import json
from random import randint

# Create a Redis client
client = redis.StrictRedis(host='103.59.95.141', port=6379, db=0)

# Define a Python dictionary
while True:
    information = {
        "latitude": randint(1,10),
        "logitude": randint(1,10),
        "cog": randint(1,10),
        "sog": randint(1,10),
    }

    # Convert the dictionary to a JSON string and set it in Redis
    client.set('username', json.dumps(information))
    print(information)
