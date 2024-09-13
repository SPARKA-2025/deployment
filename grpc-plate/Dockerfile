FROM base-sparka-api-image:latest

WORKDIR /app

COPY . .

RUN pip uninstall -y protobuf

RUN pip install grpcio grpcio-tools

EXPOSE 50051

CMD ["python", "grpc-plate-server.py"]