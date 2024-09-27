FROM python:3.9-slim

# Set up work directory
WORKDIR /app

# Install dependencies
COPY . .
RUN pip install -r requirements.txt

# Command to run the app
CMD ["python", "rabbitmq_consumer.py"]