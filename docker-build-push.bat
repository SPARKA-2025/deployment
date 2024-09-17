@echo off
REM Build image
docker build -t influxdb-gateway influxdb
docker build -t minio-gateway minio
docker build -t react-dashboard-app react-dashboard-app
docker build -t sparka-api sparka-server-api
docker build -t sparka-auth-service auth-service
docker build -t python-monitoring python-monitoring
docker build -t grpc-ocr-server grpc-ocr 
docker build -t grpc-plate-server grpc-plate 
docker build -t grpc-vehicle-server grpc-vehicle 
docker build -t ampq-minio-consumer ampq-minio
docker build -t ampq-influxdb-consumer ampq-influxdb

REM Rename image
docker tag influxdb-gateway docker.io/equehours/influxdb-gateway
docker tag minio-gateway docker.io/equehours/minio-gateway
docker tag react-dashboard-app docker.io/equehours/react-dashboard-app
docker tag sparka-api docker.io/equehours/sparka-api
docker tag sparka-auth-service docker.io/equehours/sparka-auth-service
docker tag python-monitoring docker.io/equehours/python-monitoring
docker tag grpc-ocr-server docker.io/equehours/grpc-ocr-server
docker tag grpc-plate-server docker.io/equehours/grpc-plate-server
docker tag grpc-vehicle-server docker.io/equehours/grpc-vehicle-server
docker tag ampq-minio-consumer docker.io/equehours/ampq-minio-consumer
docker tag ampq-influxdb-consumer docker.io/equehours/ampq-influxdb-consumer

REM Push image
docker push docker.io/equehours/influxdb-gateway
docker push docker.io/equehours/minio-gateway
docker push docker.io/equehours/react-dashboard-app
docker push docker.io/equehours/sparka-api
docker push docker.io/equehours/sparka-auth-service
docker push docker.io/equehours/python-monitoring
docker push docker.io/equehours/grpc-ocr-server
docker push docker.io/equehours/grpc-plate-server
docker push docker.io/equehours/grpc-vehicle-server
docker push docker.io/equehours/ampq-minio-consumer
docker push docker.io/equehours/ampq-influxdb-consumer
