FROM python:3.9-slim

RUN pip install flask flask-cors flask-jwt

WORKDIR /app

COPY . .

EXPOSE 5003

CMD ["python", "auth_server.py"]