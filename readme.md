# Optical Character Recognition Operations System 
## Arsitektur Sistem

![System Architecture](https://github.com/user-attachments/assets/940e3eaf-4436-4810-bf9b-02020d6e7cd8)


Arsitektur sistem yang ditampilkan pada diagram menggambarkan aliran data dan komponen yang terlibat dalam sebuah sistem berbasis kontainer dan lingkungan lokal yang mendukung penerapan pencatatan dan analisis data dari berbagai sumber. Berikut adalah penjelasan detail dari setiap komponen:

### Notes
- Kuning: To Do
- Hijau: Need Config
- Dokumentasi lainnya menyusul

### Container Environment

#### NGINX Rule HTTP:
Berfungsi sebagai server HTTP yang mengelola permintaan dari klien dan mengarahkan permintaan ke komponen yang relevan di dalam lingkungan kontainer, khususnya untuk memproses gambar.

#### Plate OCR Server (Flask)
Komponen ini bertanggung jawab untuk memproses gambar yang diterima dari NGINX dan melakukan Optical Character Recognition (OCR) pada pelat nomor kendaraan. Hasil prediksi dikirimkan ke Scraper Gateway Flask, dan aset gambar dikirim ke Min.io Gateway.

#### Resource Profiling Scraper (Flask)
Komponen ini mengumpulkan data profil sumber daya seperti CPU dan RAM per core. Data ini dikirimkan ke Scraper Gateway Flask untuk diproses lebih lanjut.

#### Scraper Gateway Flask
Bertindak sebagai pusat pengumpulan data dari berbagai sumber, seperti hasil prediksi dari Plate OCR Server dan data sumber daya dari Resource Profiling Scraper. Data yang diterima diteruskan ke InfluxDB Gateway untuk disimpan.

#### Min.io Gateway
Komponen ini berfungsi untuk mengelola aset gambar yang diunggah oleh Plate OCR Server dan menyimpannya ke Min.io Object Storage Server. Selain itu, ia juga mengambil data gambar untuk ditampilkan di dashboard.

#### Min.io Object Storage Server
Menyediakan penyimpanan objek untuk aset gambar dan data terkait. Ini adalah tempat penyimpanan utama untuk gambar yang dihasilkan oleh sistem OCR.

#### InfluxDB Gateway
Mengelola komunikasi antara Scraper Gateway Flask dan InfluxDB Database Server. Ini menyimpan data yang dikumpulkan dalam basis data time-series.

#### InfluxDB Database Server
Penyimpanan data time-series untuk data yang dikumpulkan, seperti data penggunaan sumber daya dan hasil pemrosesan lainnya.

#### Grafana
Alat visualisasi yang mengambil data dari InfluxDB Database Server dan menyajikannya dalam bentuk dashboard untuk analisis lebih lanjut.

#### React App Dashboard
Antarmuka pengguna yang menampilkan data yang diambil dari Min.io Gateway dan InfluxDB Gateway. Pengguna dapat melihat hasil pemrosesan data, gambar, dan metrik lainnya di sini.

#### Auth Service SSO
Mengelola dan memberikan token ke aplikasi untuk dapat mengakses sumber daya yang diizinkan.

#### Prometheus
Menyediakan gateway dan database untuk dapat ditampilkan pada grafana

#### Node Exporter
Menyediakan metrics sumber daya dari host ke sistem prometheus untuk bisa dilakukan scraping

### Local Environment
#### Redis
Penyimpanan data in-memory yang digunakan untuk mengelola antrean atau cache data sementara yang dibutuhkan oleh komponen-komponen lain di lingkungan lokal.

#### Deployment Redis Scraper

Komponen ini mengambil data dari Redis yang digunakan dalam proses deployment atau pemantauan, bagian ini yang melakukan request ke server.

#### RSTP Scraper
Mengambil data dari sumber RTSP (Real-Time Streaming Protocol) dan menyimpannya ke Redis untuk diakses oleh komponen lain seperti Deployment Redis Scraper

### Summary 
Secara keseluruhan, arsitektur ini menunjukkan sebuah sistem yang mengumpulkan, memproses, menyimpan, dan menampilkan data dari berbagai sumber, dengan beberapa komponen yang diatur dalam lingkungan kontainer dan beberapa lainnya dalam lingkungan lokal. Aliran data difasilitasi oleh komponen-komponen seperti gateway dan database, sementara visualisasi dan akses data dilakukan melalui dashboard React dan Grafana.

### Monitoring UI 

#### Grafana
Dashboard grafana memberikan informasi terkait log deteksi dan penggunaan sumber daya kontainer
![Grafana](https://github.com/user-attachments/assets/6d198fa8-c46c-4fff-ba56-b2670fa62b21)

#### Dashboard App
Dashboard app memberikan informasi terkait log deteksi beserta gambar dari deteksi
![React Dashboard App](https://github.com/user-attachments/assets/c1c9a5da-ba73-4476-b173-7f4dd6dc6baf)

## Menjalankan ekosistem operations
### Menjalankan semua aplikasi
```
docker compose up
```
### Modifikasi docker engine untuk profiling
```
{
  "experimental": true,
  "metrics-addr": "127.0.0.1:9323"
}
```
## Port mapping information

- 3000 Grafana
- 5000 InfluxDB Gateway
- 5001 Sparka-API
- 5002 Minio Gateway
- 5003 Auth Service SSO
- 5137 React App
- 8086 InfluxDB Server Database
- 9000 Minio API Server
- 9091 Prometheus
- 9101 Node Exporter
- 50051 gRPC Vehicle Server
- 50052 gRPC Plate Server
- 50053 gRPC OCR Server
