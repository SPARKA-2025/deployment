FROM equehours/grpc-ocr-server:latest

WORKDIR /app

# Install missing dependencies
RUN pip install --no-cache-dir paddleocr opencv-python-headless

COPY . .

EXPOSE 50052

CMD ["python", "grpc-ocr-server.py"]