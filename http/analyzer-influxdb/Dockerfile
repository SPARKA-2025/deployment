FROM bitnami/spark:3.5.1

RUN pip install py4j flask influxdb_client numpy 

COPY connect.py .

CMD python connect.py