FROM equehours/base-sparka-api-image:arm64

WORKDIR /app

COPY . .

EXPOSE 50052

CMD ["python", "grpc-plate-server.py"]