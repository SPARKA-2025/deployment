FROM equehours/base-sparka-api-image

WORKDIR /app

RUN pip install kafka-python

COPY . .

EXPOSE 5101

CMD ["python", "server.py"]
