FROM python:3.10-slim

RUN pip install minio flask flask-cors

WORKDIR /app

COPY . .

EXPOSE 5002

CMD ["python", "minio_server.py"]