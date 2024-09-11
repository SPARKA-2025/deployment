FROM python:3.9-slim

RUN pip install psutil requests

WORKDIR /app

COPY . .

CMD ["python", "resource_scraper.py"]