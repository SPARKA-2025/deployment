@echo off
REM Build image
@REM docker build -t influxdb-gateway ./http/influxdb
@REM docker build -t minio-gateway ./http/minio
@REM docker build -t sparka-api ./http/sparka-server-api
docker build -t sparka-auth-service ./http/auth-service
@REM docker build -t python-monitoring ./http/python-monitoring
@REM docker build -t grpc-ocr-server ./http/grpc-ocr 
@REM docker build -t grpc-plate-server ./http/grpc-plate 
@REM docker build -t grpc-vehicle-server ./http/grpc-vehicle 
@REM docker build -t ampq-minio-consumer ./message-broker/ampq-minio
@REM docker build -t ampq-influxdb-consumer ./message-broker/ampq-influxdb
docker build -t dashboard-nextjs ./http/dashboard-nextjs

REM Rename image
@REM docker tag influxdb-gateway docker.io/equehours/influxdb-gateway
@REM docker tag minio-gateway docker.io/equehours/minio-gateway
@REM docker tag sparka-api docker.io/equehours/sparka-api
docker tag sparka-auth-service docker.io/equehours/sparka-auth-service
@REM docker tag python-monitoring docker.io/equehours/python-monitoring
@REM docker tag grpc-ocr-server docker.io/equehours/grpc-ocr-server
@REM docker tag grpc-plate-server docker.io/equehours/grpc-plate-server
@REM docker tag grpc-vehicle-server docker.io/equehours/grpc-vehicle-server
@REM docker tag ampq-minio-consumer docker.io/equehours/ampq-minio-consumer
@REM docker tag ampq-influxdb-consumer docker.io/equehours/ampq-influxdb-consumer
docker tag dashboard-nextjs docker.io/equehours/dashboard-nextjs

REM Push image
@REM docker push docker.io/equehours/influxdb-gateway
@REM docker push docker.io/equehours/minio-gateway
@REM docker push docker.io/equehours/sparka-api
docker push docker.io/equehours/sparka-auth-service
@REM docker push docker.io/equehours/python-monitoring
@REM docker push docker.io/equehours/grpc-ocr-server
@REM docker push docker.io/equehours/grpc-plate-server
@REM docker push docker.io/equehours/grpc-vehicle-server
@REM docker push docker.io/equehours/ampq-minio-consumer
@REM docker push docker.io/equehours/ampq-influxdb-consumer
docker push docker.io/equehours/dashboard-nextjs
