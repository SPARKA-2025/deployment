FROM base-sparka-api-image:latest

WORKDIR /app

COPY . .

RUN pip install flask-cors

RUN pip uninstall -y protobuf

RUN pip install grpcio==1.49.0 grpcio-tools==1.49.0

EXPOSE 5001

CMD ["python", "server.py"]
