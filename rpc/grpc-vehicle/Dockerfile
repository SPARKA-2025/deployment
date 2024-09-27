FROM equehours/base-sparka-api-image:arm64

WORKDIR /app

COPY . .

EXPOSE 50051

CMD ["python", "grpc-vehicle-server.py"]