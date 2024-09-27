FROM python:3.9-slim

RUN pip install influxdb_client flask flask-cors flask-jwt

WORKDIR /app

COPY . .

EXPOSE 5000

CMD ["python", "influxdb_server.py"]