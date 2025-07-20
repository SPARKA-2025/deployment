# SPARKA Streaming Server

Server streaming untuk konversi RTSP ke HLS dalam sistem SPARKA (Smart Parking System).

## Fitur

- **Konversi RTSP ke HLS**: Mengkonversi stream RTSP dari kamera CCTV menjadi format HLS yang dapat diputar di browser
- **Manajemen Stream**: API untuk memulai, menghentikan, dan memantau status stream
- **Redis Integration**: Menyimpan informasi stream aktif di Redis untuk performa yang optimal
- **Auto Cleanup**: Otomatis membersihkan file HLS yang tidak digunakan
- **CORS Support**: Mendukung Cross-Origin Resource Sharing untuk integrasi frontend

## Teknologi

- **Node.js**: Runtime JavaScript
- **Express.js**: Web framework
- **FFmpeg**: Media processing untuk konversi RTSP ke HLS
- **Redis**: In-memory database untuk caching
- **Docker**: Containerization

## API Endpoints

### 1. Start Stream
```
POST /api/stream/start
Content-Type: application/json

{
  "rtsp_url": "rtsp://example.com/stream",
  "stream_id": "unique_stream_id"
}
```

### 2. Stop Stream
```
POST /api/stream/stop
Content-Type: application/json

{
  "stream_id": "unique_stream_id"
}
```

### 3. Get Stream Status
```
GET /api/stream/status/:stream_id
```

### 4. List Active Streams
```
GET /api/stream/list
```

### 5. Get HLS Playlist
```
GET /hls/:stream_id/index.m3u8
```

### 6. Get HLS Segments
```
GET /hls/:stream_id/:segment
```

## Instalasi

### Menggunakan Docker (Recommended)

1. Build dan jalankan dengan docker-compose:
```bash
cd /path/to/sparka/deployment
docker-compose -f docker-compose-sparka-integrated.yml up -d sparka-streaming
```

### Manual Installation

1. Install dependencies:
```bash
npm install
```

2. Install FFmpeg:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Windows (menggunakan chocolatey)
choco install ffmpeg

# macOS (menggunakan homebrew)
brew install ffmpeg
```

3. Setup Redis:
```bash
# Ubuntu/Debian
sudo apt install redis-server

# Windows
# Download dan install Redis dari https://redis.io/download

# macOS
brew install redis
```

4. Jalankan server:
```bash
npm start
```

## Konfigurasi

Server dapat dikonfigurasi melalui environment variables:

- `PORT`: Port server (default: 8005)
- `REDIS_HOST`: Host Redis (default: localhost)
- `REDIS_PORT`: Port Redis (default: 6379)
- `HLS_PATH`: Path untuk menyimpan file HLS (default: ./hls)
- `SEGMENT_DURATION`: Durasi segment HLS dalam detik (default: 2)
- `PLAYLIST_SIZE`: Jumlah segment dalam playlist (default: 3)

## Integrasi dengan SPARKA

### Backend Integration

Streaming server terintegrasi dengan backend Laravel melalui `StreamingController`:

```php
// Memulai stream
POST /admin/streaming/start
{
    "cctv_id": 1
}

// Menghentikan stream
POST /admin/streaming/stop
{
    "cctv_id": 1
}

// Mendapatkan URL streaming
GET /admin/streaming/url/{cctv_id}
```

### Frontend Integration

Frontend menggunakan HLS.js untuk memutar stream:

```javascript
import Hls from 'hls.js';

if (Hls.isSupported()) {
  const hls = new Hls();
  hls.loadSource(streamingUrl);
  hls.attachMedia(video);
}
```

## Monitoring

### Health Check
```
GET /health
```

### Stream Statistics
```
GET /api/stream/stats
```

## Troubleshooting

### Stream tidak bisa dimulai
1. Pastikan URL RTSP valid dan dapat diakses
2. Periksa log FFmpeg untuk error
3. Pastikan Redis berjalan
4. Periksa disk space untuk menyimpan file HLS

### Stream terputus-putus
1. Periksa koneksi jaringan ke sumber RTSP
2. Sesuaikan parameter segment duration
3. Periksa resource CPU dan memory

### Browser tidak bisa memutar stream
1. Pastikan browser mendukung HLS atau HLS.js terinstall
2. Periksa CORS configuration
3. Pastikan file HLS dapat diakses melalui HTTP

## Logs

Log server tersimpan di:
- Container: `/app/logs/`
- Host: `./logs/` (jika menggunakan volume mapping)

Log FFmpeg tersimpan terpisah untuk setiap stream di:
- `./logs/ffmpeg_[stream_id].log`

## Security

- Server hanya menerima koneksi dari IP yang diizinkan (konfigurasi di nginx)
- Validasi input untuk mencegah injection attacks
- Rate limiting untuk API endpoints
- Automatic cleanup untuk mencegah disk space exhaustion

## Performance

- Gunakan Redis untuk caching metadata stream
- Cleanup otomatis file HLS yang tidak digunakan
- Monitoring resource usage
- Load balancing untuk multiple instances

## Development

### Running in Development Mode
```bash
npm run dev
```

### Testing
```bash
npm test
```

### Debugging
Set environment variable `DEBUG=true` untuk verbose logging.

## License

MIT License - Lihat file LICENSE untuk detail lengkap.