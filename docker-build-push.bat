@echo off
REM Build image
docker build -t influxdb-gateway influxdb
docker build -t minio-gateway minio
docker build -t react-dashboard-app react-dashboard-app
docker build -t sparka-api sparka-server-api
docker build -t sparka-auth-service auth-service

REM Rename image
docker tag influxdb-gateway docker.io/equehours/influxdb-gateway
docker tag minio-gateway docker.io/equehours/minio-gateway
docker tag react-dashboard-app docker.io/equehours/react-dashboard-app
docker tag sparka-api docker.io/equehours/sparka-api
docker tag sparka-auth-service docker.io/equehours/sparka-auth-service

REM Push image
docker push docker.io/equehours/influxdb-gateway
docker push docker.io/equehours/minio-gateway
docker push docker.io/equehours/react-dashboard-app
docker push docker.io/equehours/sparka-api
docker push docker.io/equehours/sparka-auth-service