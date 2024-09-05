FROM python:3.10-slim

RUN pip install influxdb_client flask

WORKDIR /app

COPY . .

EXPOSE 5000

CMD ["python", "influxdb_server.py"]