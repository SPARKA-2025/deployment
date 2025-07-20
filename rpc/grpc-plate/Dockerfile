FROM equehours/grpc-plate-server:latest

WORKDIR /app

# Install missing dependencies
RUN pip install --no-cache-dir opencv-python-headless

COPY . .

EXPOSE 50053

CMD ["python", "grpc-plate-server.py"]