import requests
import matplotlib.pyplot as plt
import json

array = []
num = 1000

for i in range(num):
    response = requests.get("http://localhost:80/performance").json()
    print(response)
    array.append(response['score'])

plt.plot(array)

# Add labels and title
plt.xlabel('Index')
plt.ylabel('Value')
plt.title('Array Plot')

# Show the plot
plt.show()

with open('array.json', 'w') as json_file:
    json.dump(array, json_file)