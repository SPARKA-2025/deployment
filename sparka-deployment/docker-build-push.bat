@echo off
REM Build image
@REM docker build -t influxdb-gateway ./http/influxdb
@REM docker build -t minio-gateway ./http/minio
@REM docker build -t sparka-api ./http/sparka-server-api
@REM docker build -t sparka-auth-service ./http/auth-service
@REM docker build -t python-monitoring ./http/python-monitoring
@REM docker build -t grpc-ocr-server ./http/grpc-ocr 
@REM docker build -t grpc-plate-server ./http/grpc-plate 
@REM docker build -t grpc-vehicle-server ./http/grpc-vehicle 
@REM docker build -t ampq-minio-consumer ./message-broker/ampq-minio
@REM docker build -t ampq-influxdb-consumer ./message-broker/ampq-influxdb
@REM docker build -t dashboard-nextjs ./http/dashboard-nextjs
@REM docker build -t kafka-sparka-api ./message-broker/kafka-sparka-api
docker build -t analyzer-influxdb ./http/analyzer-influxdb

REM Rename image
@REM docker tag influxdb-gateway docker.io/equehours/influxdb-gateway
@REM docker tag minio-gateway docker.io/equehours/minio-gateway
@REM docker tag sparka-api docker.io/equehours/sparka-api
@REM docker tag sparka-auth-service docker.io/equehours/sparka-auth-service
@REM docker tag python-monitoring docker.io/equehours/python-monitoring
@REM docker tag grpc-ocr-server docker.io/equehours/grpc-ocr-server
@REM docker tag grpc-plate-server docker.io/equehours/grpc-plate-server
@REM docker tag grpc-vehicle-server docker.io/equehours/grpc-vehicle-server
@REM docker tag ampq-minio-consumer docker.io/equehours/ampq-minio-consumer
@REM docker tag ampq-influxdb-consumer docker.io/equehours/ampq-influxdb-consumer
@REM docker tag dashboard-nextjs docker.io/equehours/dashboard-nextjs
@REM docker tag kafka-sparka-api docker.io/equehours/kafka-sparka-api
docker tag analyzer-influxdb docker.io/equehours/analyzer-influxdb

REM Push image
@REM docker push docker.io/equehours/influxdb-gateway
@REM docker push docker.io/equehours/minio-gateway
@REM docker push docker.io/equehours/sparka-api
@REM docker push docker.io/equehours/sparka-auth-service
@REM docker push docker.io/equehours/python-monitoring
@REM docker push docker.io/equehours/grpc-ocr-server
@REM docker push docker.io/equehours/grpc-plate-server
@REM docker push docker.io/equehours/grpc-vehicle-server
@REM docker push docker.io/equehours/ampq-minio-consumer
@REM docker push docker.io/equehours/ampq-influxdb-consumer
@REM docker push docker.io/equehours/dashboard-nextjs
@REM docker push docker.io/equehours/kafka-sparka-api
docker push docker.io/equehours/analyzer-influxdb
