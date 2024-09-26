FROM --platform=linux/arm64 equehours/base-sparka-api-image:arm64

WORKDIR /app

COPY . .

EXPOSE 5001

CMD ["python", "server.py"]
