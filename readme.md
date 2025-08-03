# SPARKA Deployment Guide

Panduan deployment untuk sistem SPARKA dengan dua mode: **Full Docker** dan **Development Mode**.

## 📋 Prerequisites

Sebelum memulai, pastikan sistem Anda memiliki:

### Untuk Full Docker Mode:
- Docker Desktop atau Docker Engine
- Docker Compose v2.0+
- Minimum 4GB RAM
- Port 80, 3000, 3306, 6379, 8000, 8030, 8010 tersedia

### Untuk Development Mode:
- Docker Desktop atau Docker Engine
- Docker Compose v2.0+
- PHP 8.1+ dengan extensions: mbstring, xml, curl, zip, gd, mysql
- Composer
- Node.js 18+ dan npm
- Python 3.8+ (untuk SPARKA Integration Service)
- Minimum 4GB RAM
- Port 3000, 3001, 3306, 5000-5004, 6379, 8000, 8010, 8011, 8030, 8086, 9000, 9001, 15672, 50051-50053 tersedia

## ⚡ Quick Start - Development Mode

Untuk development lokal dengan frontend dan backend lokal:

```bash
# 1. Start infrastructure services
cd deployment
docker-compose -f docker-compose.dev.yml up -d

# 2. Setup backend (terminal baru)
cd ../backend
composer install && cp .env.example .env
# Edit .env sesuai konfigurasi database
php artisan key:generate && php artisan migrate && php artisan db:seed
php artisan serve --port=8000

# 3. Setup frontend (terminal baru)
cd ../frontend
npm install && cp .env.example .env.local
# Edit .env.local sesuai konfigurasi
npm run dev
```

**Akses aplikasi**: http://localhost:3000

## 🚀 Fitur Utama

- **Full Docker Deployment**: Semua layanan berjalan dalam containers
- **AI Integration Service**: Deteksi plat nomor otomatis dengan auto-entry/exit
- **Development Mode**: Infrastruktur dalam Docker, aplikasi lokal
- **Auto Database Migration**: Inisialisasi database otomatis
- **Health Checks**: Monitoring kesehatan semua layanan
- **Load Balancing**: Nginx untuk distribusi traffic
- **Persistent Storage**: Data MySQL dan Redis tersimpan permanen
- **Real-time Processing**: Streaming video dan image processing
- **Auto-Exit Logic**: Deteksi otomatis kendaraan keluar berdasarkan timeout

## 🚀 Mode Deployment

### 1. Full Docker Mode (Production)

Menjalankan semua services termasuk AI Integration (Frontend, Backend, Streaming, MySQL, Redis, Nginx) dalam Docker containers.

```bash
cd deployment
docker-compose -f docker-compose-main.yml up -d

# Tunggu MySQL siap, lalu jalankan migrasi
docker-compose -f docker-compose-main.yml exec sparka-backend php artisan migrate --force
docker-compose -f docker-compose-main.yml exec sparka-backend php artisan db:seed --force
```

**Layanan yang berjalan:**
- MySQL Database (port 3306)
- Redis Cache (port 6379)
- SPARKA Backend Laravel (port 8000)
- SPARKA Frontend Next.js (port 3000)
- Streaming Server Node.js (port 8010)
- **SPARKA Integration Service (port 8004)** - AI Detection & Auto Parking Management
- Nginx Load Balancer (port 80)

**URL Akses:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Streaming: http://localhost:8010
- Integration Service: http://localhost:8004
- Load Balancer: http://localhost:80

### 2. Development Mode (Frontend & Backend Lokal)

Mode ini ideal untuk development harian dimana Frontend dan Backend dijalankan secara lokal dengan hot reload, sementara infrastruktur (database, redis, dll) berjalan dalam Docker.

#### Langkah 1: Start Infrastructure Services
```bash
cd deployment
docker-compose -f docker-compose.dev.yml up -d
```

#### Langkah 2: Setup Backend Laravel (Terminal 1)
```bash
cd ../backend
composer install
cp .env.example .env

# Edit file .env dengan konfigurasi berikut:
# DB_HOST=localhost
# DB_PORT=3306
# DB_DATABASE=sparka_db
# DB_USERNAME=sparka_user
# DB_PASSWORD=sparka_password
# REDIS_HOST=localhost
# REDIS_PORT=6379

# Jalankan migrasi dan seeding
php artisan key:generate
php artisan migrate
php artisan db:seed

# Start Laravel development server
php artisan serve --port=8000
```

#### Langkah 3: Setup Frontend Next.js (Terminal 2)
```bash
cd ../frontend
npm install
cp .env.example .env.local

# Edit file .env.local dengan konfigurasi berikut:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api
# NEXT_PUBLIC_APP_URL=http://localhost:3000

# Start Next.js development server
npm run dev
```

#### Langkah 4: Integration Service (Opsional - Terminal 3)
```bash
cd deployment
pip install -r requirements.txt
python sparka_integration_service.py
```

**Layanan Docker:**
- MySQL Database (port 3306)
- Redis Cache (port 6379)
- Streaming Server Node.js (port 8010, 8011)
- SPARKA Integration Service (port 8030)
- SPARKA Server API (port 5000)
- MinIO Object Storage (port 9000, 9001)
- RabbitMQ (port 5672, 15672)
- InfluxDB (port 8086)
- Grafana (port 3001)
- gRPC Services (OCR: 50051, Plate: 50052, Vehicle: 50053)
- Auth Service (port 5004)
- InfluxDB Service (port 5003)
- MinIO Service (port 5001)

**URL Akses Development:**
- Frontend: http://localhost:3000 (lokal)
- Backend API: http://localhost:8000/api (lokal)
- MySQL: localhost:3306
- Redis: localhost:6379
- SPARKA Integration Service: http://localhost:8030
- SPARKA Server API: http://localhost:5000
- Streaming Server: http://localhost:8010
- MinIO Console: http://localhost:9001
- RabbitMQ Management: http://localhost:15672
- InfluxDB: http://localhost:8086
- Grafana: http://localhost:3001

#### Tips Development Mode:
- **Hot Reload**: Frontend dan Backend akan otomatis reload saat ada perubahan code
- **Database Persistent**: Data database tersimpan dalam Docker volume
- **Debugging**: Gunakan debugger IDE untuk Backend Laravel dan Frontend Next.js
- **API Testing**: Gunakan Postman atau tools serupa untuk test API di http://localhost:8000/api

#### Menghentikan Development Mode:
```bash
# Stop infrastructure services
cd deployment
docker-compose -f docker-compose.dev.yml down

# Stop Backend dan Frontend dengan Ctrl+C di masing-masing terminal
```

## 📁 Struktur Deployment

```
deployment/
├── docker-compose-main.yml    # Full Docker deployment
├── docker-compose.dev.yml     # Development mode (DB only)
├── config/
│   ├── nginx/                  # Nginx configuration
│   ├── mysql/                  # MySQL configuration
│   └── ...
├── streaming-server/           # Node.js streaming server
├── logs/                       # Application logs
└── storage/                    # Persistent storage
```

## 🤖 SPARKA Integration Service

SPARKA Integration Service menyediakan deteksi plat nomor otomatis dan manajemen parkir cerdas.

### Endpoint API Integration Service

**Base URL**: `http://localhost:8030`

- `GET /health` - Health check service
- `GET /stats` - Statistik deteksi dan performa
- `POST /process-image` - Upload dan proses gambar untuk deteksi plat
- `POST /process-video` - Upload dan proses video untuk deteksi plat
- `POST /process-rtsp` - Proses RTSP stream real-time
- `POST /test-integration` - Test integrasi dengan backend
- `GET /config/auto-exit` - Konfigurasi auto-exit timeout
- `POST /config/auto-exit` - Update auto-exit timeout
- `POST /config/auto-exit/test` - Test fungsi auto-exit

### Fitur Auto-Exit Logic

Sistem secara otomatis mendeteksi kendaraan keluar berdasarkan:
- **Timeout Detection**: Jika kendaraan terdeteksi lagi setelah timeout (default: 5 menit), dianggap sebagai EXIT
- **Redis Caching**: Menyimpan waktu deteksi terakhir untuk setiap plat nomor
- **Smart Entry/Exit**: Otomatis menentukan apakah kendaraan masuk atau keluar

### Contoh Penggunaan

```bash
# Test health
curl http://localhost:8030/health

# Upload gambar untuk deteksi
curl -X POST -F "file=@image.jpg" http://localhost:8030/process-image

# Lihat statistik
curl http://localhost:8030/stats

# Test integrasi
curl -X POST http://localhost:8030/test-integration
```

## 🔧 Management Commands

### Full Docker Mode
```bash
# Stop all services
docker-compose -f docker-compose-main.yml down

# View logs
docker-compose -f docker-compose-main.yml logs -f sparka-backend
docker-compose -f docker-compose-main.yml logs -f sparka-frontend
docker-compose -f docker-compose-main.yml logs -f sparka-integration

# Restart specific service
docker-compose -f docker-compose-main.yml restart sparka-backend
docker-compose -f docker-compose-main.yml restart sparka-integration

# Access container shell
docker-compose -f docker-compose-main.yml exec sparka-backend bash
```

### Development Mode
```bash
# Stop database services
docker-compose -f docker-compose.dev.yml down

# View database logs
docker-compose -f docker-compose.dev.yml logs -f mysql

# Access MySQL
docker-compose -f docker-compose.dev.yml exec mysql mysql -u sparka_user -p sparka_db
```

## 🔒 Environment Variables

### Development Mode Configuration

#### Backend Laravel (.env)
```env
APP_NAME=SPARKA
APP_ENV=local
APP_KEY=base64:your-app-key-here
APP_DEBUG=true
APP_URL=http://localhost:8000

DB_CONNECTION=mysql
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=sparka_db
DB_USERNAME=sparka_user
DB_PASSWORD=sparka_password

REDIS_HOST=localhost
REDIS_PASSWORD=null
REDIS_PORT=6379

MAIL_MAILER=smtp
MAIL_HOST=mailhog
MAIL_PORT=1025
```

#### Frontend Next.js (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_STREAMING_URL=http://localhost:8010
NEXT_PUBLIC_INTEGRATION_SERVICE_URL=http://localhost:8030
NEXT_PUBLIC_SERVER_API_URL=http://localhost:5000
```

#### Deployment (.env)
Konfigurasi environment untuk Docker services tersedia di file `.env` di root folder deployment.

## 🐛 Troubleshooting

### Development Mode Issues

#### Database Connection Issues
```bash
# Check MySQL status
docker-compose -f docker-compose.dev.yml ps mysql

# Check MySQL logs
docker-compose -f docker-compose.dev.yml logs mysql

# Test database connection
docker-compose -f docker-compose.dev.yml exec mysql mysql -u sparka_user -p sparka_db
```

#### Laravel Backend Issues
```bash
# Clear Laravel cache
php artisan config:clear
php artisan cache:clear
php artisan route:clear

# Check Laravel logs
tail -f storage/logs/laravel.log

# Reset database
php artisan migrate:fresh --seed
```

#### Next.js Frontend Issues
```bash
# Clear Next.js cache
rm -rf .next
npm run build

# Check if API connection works
curl http://localhost:8000/api/health
```

#### Port Conflicts
Jika ada konflik port, edit file `.env` dan ubah port yang diperlukan:
```
DB_PORT=3307
REDIS_PORT=6380
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

#### Common Development Issues
- **Composer dependencies**: Jalankan `composer install` di folder backend
- **NPM dependencies**: Jalankan `npm install` di folder frontend
- **Database tidak terkoneksi**: Pastikan Docker services berjalan dengan `docker-compose -f docker-compose.dev.yml ps`
- **Permission issues**: Pastikan folder storage/ dan bootstrap/cache/ writable di Laravel

## 📝 Notes

- **Development Mode** cocok untuk development harian dengan hot reload
- **Full Docker Mode** cocok untuk testing, staging, dan production
- Semua konfigurasi terpusat di folder `deployment/`
- Database data persisten menggunakan Docker volumes