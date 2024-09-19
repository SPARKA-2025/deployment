@echo off
REM Build image
@REM docker build -t influxdb-gateway influxdb
@REM docker build -t minio-gateway minio
@REM docker build -t react-dashboard-app react-dashboard-app
@REM docker build -t sparka-api sparka-server-api
@REM docker build -t sparka-auth-service auth-service
@REM docker build -t python-monitoring python-monitoring
@REM docker build -t grpc-ocr-server grpc-ocr 
@REM docker build -t grpc-plate-server grpc-plate 
@REM docker build -t grpc-vehicle-server grpc-vehicle 
docker build -t ampq-minio-consumer ampq-minio
docker build -t ampq-influxdb-consumer ampq-influxdb

REM Rename image
@REM docker tag influxdb-gateway docker.io/equehours/influxdb-gateway
@REM docker tag minio-gateway docker.io/equehours/minio-gateway
@REM docker tag react-dashboard-app docker.io/equehours/react-dashboard-app
@REM docker tag sparka-api docker.io/equehours/sparka-api
@REM docker tag sparka-auth-service docker.io/equehours/sparka-auth-service
@REM docker tag python-monitoring docker.io/equehours/python-monitoring
@REM docker tag grpc-ocr-server docker.io/equehours/grpc-ocr-server
@REM docker tag grpc-plate-server docker.io/equehours/grpc-plate-server
@REM docker tag grpc-vehicle-server docker.io/equehours/grpc-vehicle-server
docker tag ampq-minio-consumer docker.io/equehours/ampq-minio-consumer
docker tag ampq-influxdb-consumer docker.io/equehours/ampq-influxdb-consumer

REM Push image
@REM docker push docker.io/equehours/influxdb-gateway
@REM docker push docker.io/equehours/minio-gateway
@REM docker push docker.io/equehours/react-dashboard-app
@REM docker push docker.io/equehours/sparka-api
@REM docker push docker.io/equehours/sparka-auth-service
@REM docker push docker.io/equehours/python-monitoring
@REM docker push docker.io/equehours/grpc-ocr-server
@REM docker push docker.io/equehours/grpc-plate-server
@REM docker push docker.io/equehours/grpc-vehicle-server
docker push docker.io/equehours/ampq-minio-consumer
docker push docker.io/equehours/ampq-influxdb-consumer
