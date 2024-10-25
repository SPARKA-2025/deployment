FROM python:3.9-slim

RUN pip install flask flask-cors flask-jwt opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger opentelemetry-instrumentation-flask opentelemetry-exporter-otlp protobuf==3.20.*

WORKDIR /app

COPY . .

EXPOSE 5003

CMD ["python", "auth_server.py"]