-- SPARKA Database Initialization Script
-- This script will be executed automatically when MySQL container starts

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS sparka_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user if not exists
CREATE USER IF NOT EXISTS 'sparka_user'@'%' IDENTIFIED BY 'sparka123';

-- Grant privileges
GRANT ALL PRIVILEGES ON sparka_db.* TO 'sparka_user'@'%';
GRANT ALL PRIVILEGES ON sparka_db.* TO 'sparka_user'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Use the database
USE sparka_db;

-- Create basic tables if they don't exist
-- This is a fallback in case Laravel migrations haven't run yet

CREATE TABLE IF NOT EXISTS `migrations` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `migration` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `batch` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `users` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email_verified_at` timestamp NULL DEFAULT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `remember_token` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_email_unique` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user if not exists
INSERT IGNORE INTO `users` (`id`, `name`, `email`, `password`, `created_at`, `updated_at`) VALUES
(1, 'Admin SPARKA', 'admin@sparka.com', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', NOW(), NOW());

-- Create areas table if not exists
CREATE TABLE IF NOT EXISTS `areas` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `nama` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `deskripsi` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default area if not exists
INSERT IGNORE INTO `areas` (`id`, `nama`, `deskripsi`, `created_at`, `updated_at`) VALUES
(1, 'Area Utama', 'Area parkir utama SPARKA', NOW(), NOW());

-- Create zones table if not exists
CREATE TABLE IF NOT EXISTS `zones` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `area_id` bigint unsigned NOT NULL,
  `nama` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `deskripsi` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `zones_area_id_foreign` (`area_id`),
  CONSTRAINT `zones_area_id_foreign` FOREIGN KEY (`area_id`) REFERENCES `areas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default zone if not exists
INSERT IGNORE INTO `zones` (`id`, `area_id`, `nama`, `deskripsi`, `created_at`, `updated_at`) VALUES
(1, 1, 'Zone A', 'Zone A di area utama', NOW(), NOW());

-- Create parts table if not exists
CREATE TABLE IF NOT EXISTS `parts` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `zone_id` bigint unsigned NOT NULL,
  `nama` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `deskripsi` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `parts_zone_id_foreign` (`zone_id`),
  CONSTRAINT `parts_zone_id_foreign` FOREIGN KEY (`zone_id`) REFERENCES `zones` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default part if not exists
INSERT IGNORE INTO `parts` (`id`, `zone_id`, `nama`, `deskripsi`, `created_at`, `updated_at`) VALUES
(1, 1, 'Part 1', 'Bagian 1 dari Zone A', NOW(), NOW());

-- Create slot_parkir table if not exists
CREATE TABLE IF NOT EXISTS `slot_parkir` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `part_id` bigint unsigned NOT NULL,
  `nomor_slot` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('kosong','terisi','rusak') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'kosong',
  `koordinat_x` int DEFAULT NULL,
  `koordinat_y` int DEFAULT NULL,
  `lebar` int DEFAULT NULL,
  `tinggi` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slot_parkir_part_id_nomor_slot_unique` (`part_id`,`nomor_slot`),
  KEY `slot_parkir_part_id_foreign` (`part_id`),
  CONSTRAINT `slot_parkir_part_id_foreign` FOREIGN KEY (`part_id`) REFERENCES `parts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create cctv_data table if not exists
CREATE TABLE IF NOT EXISTS `cctv_data` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `part_id` bigint unsigned NOT NULL,
  `nama` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `username` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` enum('aktif','nonaktif') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'aktif',
  `stream_active` tinyint(1) NOT NULL DEFAULT '0',
  `hls_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `stream_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_stream_start` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cctv_data_part_id_foreign` (`part_id`),
  KEY `idx_stream_active` (`stream_active`),
  KEY `idx_last_stream_start` (`last_stream_start`),
  CONSTRAINT `cctv_data_part_id_foreign` FOREIGN KEY (`part_id`) REFERENCES `parts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample CCTV data if not exists
INSERT IGNORE INTO `cctv_data` (`id`, `part_id`, `nama`, `url`, `status`, `created_at`, `updated_at`) VALUES
(1, 1, 'CCTV Demo', 'rtsp://demo:demo@ipvmdemo.dyndns.org:5541/onvif-media/media.amp?profile=profile_1_h264&sessiontimeout=60&streamtype=unicast', 'aktif', NOW(), NOW());

SELECT 'SPARKA Database initialized successfully!' as message;