FROM base-sparka-api-image:latest

WORKDIR /app

COPY . .

RUN pip uninstall -y protobuf

RUN pip install grpcio==1.49.0 grpcio-tools==1.49.0

EXPOSE 50053

CMD ["python", "grpc-plate-server.py"]