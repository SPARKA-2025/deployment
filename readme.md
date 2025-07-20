# SPARKA Deployment Guide

Panduan deployment untuk sistem SPARKA dengan dua mode: **Full Docker** dan **Development Mode**.

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

### 2. Development Mode

Menjalankan infrastruktur dan AI services dalam Docker, Frontend dan Backend dijalankan secara lokal.

```bash
# Start database services
cd deployment
docker-compose -f docker-compose.dev.yml up -d

# Jalankan Backend (Laravel) - Terminal 1
cd ../backend
composer install
cp .env.example .env
# Edit .env untuk koneksi database:
# DB_HOST=localhost
# DB_PORT=3306
# REDIS_HOST=localhost
# REDIS_PORT=6379
php artisan migrate
php artisan db:seed
php artisan serve --port=8000

# Jalankan Frontend (Next.js) - Terminal 2
cd ../frontend
npm install
cp .env.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm run dev

# Integration Service (opsional untuk testing AI) - Terminal 3
cd deployment
python sparka_integration_service.py
```

**Layanan Docker:**
- MySQL Database (port 3306)
- Redis Cache (port 6379)
- Streaming Server Node.js (port 3001)
- Nginx Reverse Proxy (port 80)

**URL Akses Development:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- MySQL: localhost:3306
- Redis: localhost:6379
- Integration Service: http://localhost:8004

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

## 🤖 AI Integration Service

SPARKA Integration Service menyediakan deteksi plat nomor otomatis dan manajemen parkir cerdas.

### Endpoint API Integration Service

**Base URL**: `http://localhost:8004`

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
curl http://localhost:8004/health

# Upload gambar untuk deteksi
curl -X POST -F "file=@image.jpg" http://localhost:8004/process-image

# Lihat statistik
curl http://localhost:8004/stats

# Test integrasi
curl -X POST http://localhost:8004/test-integration
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

Konfigurasi environment tersedia di file `.env` di root folder deployment.

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check MySQL status
docker-compose -f docker-compose.dev.yml ps mysql

# Check MySQL logs
docker-compose -f docker-compose.dev.yml logs mysql
```

### Port Conflicts
Jika ada konflik port, edit file `.env` dan ubah port yang diperlukan:
```
DB_PORT=3307
REDIS_PORT=6380
BACKEND_PORT=8001
```

## 📝 Notes

- **Development Mode** cocok untuk development harian dengan hot reload
- **Full Docker Mode** cocok untuk testing, staging, dan production
- Semua konfigurasi terpusat di folder `deployment/`
- Database data persisten menggunakan Docker volumes