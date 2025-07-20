#!/usr/bin/env python3
"""
SPARKA Integration Service
Menghubungkan backend SPARKA dengan AI detection services untuk automasi penuh
"""

import os
import sys
import time
import json
import logging
import requests
import cv2
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import queue
import redis
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import tempfile
from pathlib import Path
import asyncio
import aiohttp
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import grpc
from retrying import retry
import yt_dlp
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SPARKAIntegrationService:
    """Service untuk integrasi lengkap SPARKA dengan AI detection"""
    
    def __init__(self):
        # URLs konfigurasi
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        self.ai_api_url = os.getenv('AI_API_URL', 'http://sparka-ai-api:5000')
        self.vehicle_detection_url = os.getenv('VEHICLE_DETECTION_URL', 'sparka-grpc-vehicle-dev:50051')
        self.ocr_service_url = os.getenv('OCR_SERVICE_URL', 'sparka-grpc-ocr-dev:50052')
        self.plate_detection_url = os.getenv('PLATE_DETECTION_URL', 'sparka-grpc-plate-dev:50053')
        
        # Redis connection
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        try:
            self.redis_client = redis.from_url(redis_url)
            # Test Redis connection
            self.redis_client.ping()
            logger.info(f"Redis connected successfully: {redis_url}")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            # Use a mock Redis client for development
            self.redis_client = None
        
        # Flask app untuk API endpoints
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Thread pool untuk processing
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Configuration
        # Convert seconds to minutes for internal use (300 seconds = 5 minutes)
        # Note: Environment variable is in seconds, but internal logic uses minutes
        self.auto_exit_timeout_minutes = int(os.getenv('AUTO_EXIT_TIMEOUT_SECONDS', 300)) / 60
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful_detections': 0,
            'failed_detections': 0,
            'parking_updates': 0,
            'auto_exits_triggered': 0,
            'start_time': datetime.now()
        }
        
        logger.info("SPARKA Integration Service initialized")
        
    def is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube URL"""
        youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
        return any(domain in url.lower() for domain in youtube_domains)
    
    def get_youtube_stream_url(self, youtube_url: str) -> str:
        """Get direct stream URL from YouTube URL using yt-dlp"""
        try:
            ydl_opts = {
                'format': 'best[height<=720]',  # Get best quality up to 720p
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                stream_url = info.get('url')
                
                if stream_url:
                    logger.info(f"Successfully extracted stream URL from YouTube: {youtube_url}")
                    return stream_url
                else:
                    raise Exception("Could not extract stream URL")
                    
        except Exception as e:
            logger.error(f"Error extracting YouTube stream URL: {e}")
            raise Exception(f"Failed to get YouTube stream: {e}")
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'service': 'sparka-integration',
                'timestamp': datetime.now().isoformat(),
                'uptime': str(datetime.now() - self.stats['start_time']),
                'stats': self.stats
            })
            
        @self.app.route('/process-image', methods=['POST'])
        def process_image():
            return self.handle_image_processing()
            
        @self.app.route('/process-video', methods=['POST'])
        def process_video():
            return self.handle_video_processing()
            
        @self.app.route('/process-rtsp', methods=['POST'])
        def process_rtsp():
            return self.handle_rtsp_processing()
            
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """Get service statistics"""
            try:
                # Get backend parking statistics
                backend_stats = {}
                try:
                    response = requests.get(f"{self.backend_url}/ai/parking/stats", timeout=5)
                    if response.status_code == 200:
                        backend_stats = response.json().get('data', {})
                except Exception as e:
                    logger.warning(f"Could not fetch backend stats: {e}")

                stats = {
                    'service_name': 'SPARKA Integration Service',
                    'version': '1.0.0',
                    'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds(),
                    'total_processed': self.stats['total_processed'],
                    'successful_detections': self.stats['successful_detections'],
                    'failed_detections': self.stats['failed_detections'],
                    'parking_updates': self.stats['parking_updates'],
                    'backend_stats': backend_stats,
                    'timestamp': datetime.now().isoformat()
                }
                return jsonify(stats)
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return jsonify({'error': str(e)}), 500
            
        @self.app.route('/test-integration', methods=['POST'])
        def test_integration():
            return self.handle_integration_test()
            
        @self.app.route('/config/auto-exit', methods=['GET', 'POST'])
        def auto_exit_config():
            return self.handle_auto_exit_config()
            
        @self.app.route('/config/auto-exit/test', methods=['POST'])
        def test_auto_exit():
            return self.handle_test_auto_exit()
    
    def validate_indonesian_plate(self, plate_text: str) -> bool:
        """Validasi format plat nomor Indonesia"""
        import re
        
        # Format: B 1234 CD atau B1234CD
        patterns = [
            r'^[A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3}$',  # B 1234 CD
            r'^[A-Z]{1,2}\d{1,4}[A-Z]{1,3}$',        # B1234CD
        ]
        
        plate_clean = plate_text.strip().upper()
        
        for pattern in patterns:
            if re.match(pattern, plate_clean):
                return True
                
        return False
    
    def clean_plate_text(self, plate_text: str) -> str:
        """Bersihkan dan format plat nomor"""
        import re
        
        # Remove special characters and extra spaces
        cleaned = re.sub(r'[^A-Z0-9\s]', '', plate_text.upper())
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Format standard: B 1234 CD
        parts = cleaned.split()
        if len(parts) >= 3:
            # Gabungkan huruf di awal jika terpisah
            prefix = ''.join([p for p in parts if p.isalpha()][:2])
            numbers = ''.join([p for p in parts if p.isdigit()])
            suffix = ''.join([p for p in parts if p.isalpha()][1:] if len([p for p in parts if p.isalpha()]) > 1 else [p for p in parts if p.isalpha()][1:])
            
            if prefix and numbers and suffix:
                return f"{prefix} {numbers} {suffix}"
                
        return cleaned
    
    @retry(stop_max_attempt_number=3, wait_fixed=1000)
    def call_ai_detection(self, image_data: bytes) -> Dict:
        """Call AI detection service"""
        try:
            files = {'image': ('image.jpg', image_data, 'image/jpeg')}
            response = requests.post(
                f"{self.ai_api_url}/predict",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"AI API raw response: {result}")
                detections = []
                
                # AI API returns array directly
                if isinstance(result, list):
                    predictions = result
                    logger.info(f"Processing {len(predictions)} predictions from AI API")
                else:
                    predictions = []
                    logger.warning("AI API response is not a list, no predictions to process")
                
                for i, pred in enumerate(predictions):
                    logger.info(f"Processing prediction {i+1}: {pred}")
                    
                    if isinstance(pred, dict) and 'plate_number' in pred and pred['plate_number'] and pred['plate_number'] != 'No Detection':
                        logger.info(f"Valid plate found in prediction {i+1}: {pred['plate_number']}")
                        
                        # Extract confidence from vehicle detection or set default
                        confidence = 0.8  # Default confidence since AI API doesn't return confidence for plates
                        
                        # Extract bbox from plate_position if available
                        bbox = []
                        if 'plate_position' in pred:
                            plate_pos = pred['plate_position']
                            bbox = [plate_pos.get('x1', 0), plate_pos.get('y1', 0), 
                                   plate_pos.get('x2', 0), plate_pos.get('y2', 0)]
                        
                        detection = {
                            'plate_text': pred['plate_number'],
                            'confidence': confidence,
                            'bbox': bbox,
                            'vehicle_class': pred.get('vehicle_class', 'unknown'),
                            'vehicle_position': pred.get('vehicle_position', {})
                        }
                        
                        detections.append(detection)
                        logger.info(f"Added detection: {detection}")
                    else:
                        logger.info(f"Skipping prediction {i+1}: invalid or no plate detected")
                        
                logger.info(f"AI detection successful: {len(detections)} plates detected")
                return {'detections': detections}
            else:
                logger.error(f"AI detection failed: {response.status_code} - {response.text}")
                return {'detections': []}
                
        except Exception as e:
            logger.error(f"Error calling AI detection: {e}")
            raise
    
    def determine_vehicle_action(self, plate_number: str) -> str:
        """Determine if vehicle is entering or exiting based on last detection time"""
        try:
            # Check if Redis is available
            if not self.redis_client:
                logger.warning("Redis not available, defaulting to entry action")
                return 'entry'
                
            # Get last detection time from Redis
            last_detection_key = f"last_detection:{plate_number}"
            last_detection_str = self.redis_client.get(last_detection_key)
            
            # Check if vehicle was already marked as exited
            exit_status_key = f"exit_status:{plate_number}"
            exit_status = self.redis_client.get(exit_status_key)
            
            current_time = datetime.now()
            
            if last_detection_str:
                last_detection = datetime.fromisoformat(last_detection_str.decode('utf-8'))
                time_diff = (current_time - last_detection).total_seconds() / 60  # in minutes
                
                # If last detection was more than configured timeout, consider it as exit
                if time_diff >= self.auto_exit_timeout_minutes and not exit_status:
                    timeout_seconds = self.auto_exit_timeout_minutes * 60
                    time_diff_seconds = time_diff * 60
                    logger.info(f"Vehicle {plate_number} detected after {time_diff_seconds:.1f} seconds (timeout: {timeout_seconds}sec) - treating as EXIT")
                    self.stats['auto_exits_triggered'] += 1
                    
                    # Mark vehicle as exited to prevent repeated exit actions
                    try:
                        self.redis_client.setex(exit_status_key, 3600, "exited")  # 1 hour
                    except Exception as e:
                        logger.warning(f"Failed to set exit status in Redis: {e}")
                    return 'exit'
                elif exit_status:
                    # Vehicle was already marked as exited, new detection is entry
                    logger.info(f"Vehicle {plate_number} was previously exited, new detection - treating as ENTRY")
                    # Clear exit status for new entry cycle
                    try:
                        self.redis_client.delete(exit_status_key)
                    except Exception as e:
                        logger.warning(f"Failed to clear exit status in Redis: {e}")
                    return 'entry'
                else:
                    timeout_seconds = self.auto_exit_timeout_minutes * 60
                    time_diff_seconds = time_diff * 60
                    logger.info(f"Vehicle {plate_number} detected after {time_diff_seconds:.1f} seconds (timeout: {timeout_seconds}sec) - treating as ENTRY")
                    return 'entry'
            else:
                # First time detection - always entry
                logger.info(f"First time detection for {plate_number} - treating as ENTRY")
                # Clear any existing exit status
                if exit_status:
                    try:
                        self.redis_client.delete(exit_status_key)
                    except Exception as e:
                        logger.warning(f"Failed to clear exit status in Redis: {e}")
                return 'entry'
                
        except Exception as e:
            logger.error(f"Error determining vehicle action: {e}")
            return 'entry'  # Default to entry on error
    
    def update_last_detection_time(self, plate_number: str):
        """Update last detection time in Redis"""
        try:
            if not self.redis_client:
                logger.warning("Redis not available, skipping detection time update")
                return
                
            last_detection_key = f"last_detection:{plate_number}"
            current_time = datetime.now().isoformat()
            # Store for 24 hours
            self.redis_client.setex(last_detection_key, 86400, current_time)
        except Exception as e:
            logger.error(f"Error updating last detection time: {e}")

    @retry(stop_max_attempt_number=3, wait_fixed=1000)
    def update_parking_status(self, plate_number: str, action: str = None, confidence: float = 0.8, location: str = "Unknown", camera_id: str = "AI_CAMERA") -> Dict:
        """Update parking status via backend API with auto-detection of entry/exit"""
        try:
            # Clean and validate plate number
            cleaned_plate = self.clean_plate_text(plate_number)
            if not self.validate_indonesian_plate(cleaned_plate):
                logger.warning(f"Invalid plate format: {cleaned_plate}")
                return {'success': False, 'error': 'Invalid plate format'}

            # Auto-determine action if not provided
            if action is None:
                action = self.determine_vehicle_action(cleaned_plate)
            
            # Only update last detection time for entry actions
            # For exit actions, we don't update the time to preserve the auto-exit logic
            if action == 'entry':
                self.update_last_detection_time(cleaned_plate)
                logger.info(f"Entry action processed for {cleaned_plate}, detection time updated")
            elif action == 'exit':
                logger.info(f"Exit action processed for {cleaned_plate}, detection time NOT updated")

            # Prepare data for backend API
            data = {
                'plat_nomor': cleaned_plate,
                'action': action,  # 'entry' or 'exit'
                'confidence': confidence,
                'detection_time': datetime.now().isoformat(),
                'location': location,
                'camera_id': camera_id
            }
            
            # Call the new AI integration endpoint
            response = requests.post(
                f"{self.backend_url}/api/ai/parking/update-status",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                
                # Convert backend response format to integration service format
                backend_status = result.get('status', 'error')
                success = backend_status in ['success', 'warning']  # Both success and warning are considered successful
                
                formatted_result = {
                    'success': success,
                    'action': action,
                    'message': result.get('message', ''),
                    'data': result.get('data', {}),
                    'backend_status': backend_status
                }
                
                logger.info(f"Parking status updated for {cleaned_plate}: {action} - Backend status: {backend_status}")
                
                # Cache result in Redis if available
                if self.redis_client:
                    try:
                        cache_key = f"parking_update:{cleaned_plate}:{action}"
                        self.redis_client.setex(
                            cache_key, 
                            300,  # 5 minutes
                            json.dumps(formatted_result)
                        )
                    except Exception as e:
                        logger.warning(f"Failed to cache result in Redis: {e}")
                
                self.stats['parking_updates'] += 1
                return formatted_result
            else:
                logger.error(f"Failed to update parking status: {response.status_code} - {response.text}")
                return {'success': False, 'action': action, 'error': response.text, 'message': f"Backend error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error updating parking status: {e}")
            return {'success': False, 'action': action, 'error': str(e), 'message': f"Connection error: {str(e)}"}
    
    def process_image_for_plates(self, image_data: bytes, update_parking: bool = True) -> Dict:
        """Process image untuk deteksi plat nomor"""
        try:
            self.stats['total_processed'] += 1
            
            # Call AI detection
            detection_result = self.call_ai_detection(image_data)
            detections = detection_result.get('detections', [])
            
            processed_detections = []
            parking_updates = []
            
            for detection in detections:
                plate_text = detection.get('plate_text', '')
                confidence = detection.get('confidence', 0)
                
                if plate_text and confidence > 0.5:
                    # Clean and validate plate
                    cleaned_plate = self.clean_plate_text(plate_text)
                    
                    if self.validate_indonesian_plate(cleaned_plate):
                        processed_detections.append({
                            'plate_text': cleaned_plate,
                            'original_text': plate_text,
                            'confidence': confidence,
                            'bbox': detection.get('bbox', [])
                        })
                        
                        # Update parking status if enabled (auto-detect entry/exit)
                        if update_parking:
                            update_result = self.update_parking_status(cleaned_plate)
                            parking_updates.append({
                                'plate_number': cleaned_plate,
                                'action': update_result.get('action', 'unknown'),
                                'success': update_result.get('success', False),
                                'message': update_result.get('message', '')
                            })
            
            if processed_detections:
                self.stats['successful_detections'] += 1
            else:
                self.stats['failed_detections'] += 1
                
            return {
                'success': True,
                'detections': processed_detections,
                'parking_updates': parking_updates,
                'total_detections': len(processed_detections)
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            self.stats['failed_detections'] += 1
            return {
                'success': False,
                'error': str(e),
                'detections': [],
                'parking_updates': []
            }
    
    def process_video_for_plates(self, video_path: str, update_parking: bool = True) -> Dict:
        """Process video untuk deteksi plat nomor"""
        try:
            self.stats['total_processed'] += 1
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Cannot open video file")
                
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sample frames every 2 seconds
            frame_interval = max(1, fps * 2)
            
            all_detections = []
            unique_plates = set()
            parking_updates = []
            plate_last_seen = {}  # Track when each plate was last processed
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                if frame_count % frame_interval == 0:
                    current_time = time.time()
                    
                    # Convert frame to bytes
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_data = buffer.tobytes()
                    
                    # Process frame with parking updates enabled
                    result = self.process_image_for_plates(image_data, update_parking)
                    
                    # Log frame processing results
                    frame_detections = result.get('detections', [])
                    if frame_detections:
                        logger.info(f"Frame {frame_count}: Found {len(frame_detections)} detections")
                        for det in frame_detections:
                            logger.info(f"  - Plate: {det.get('plate_text', 'unknown')} (confidence: {det.get('confidence', 0):.2f})")
                    
                    # Collect all detections and parking updates
                    for detection in frame_detections:
                        plate_text = detection['plate_text']
                        
                        # Allow re-detection of same plate after 30 seconds
                        should_process = True
                        if plate_text in plate_last_seen:
                            time_since_last = current_time - plate_last_seen[plate_text]
                            if time_since_last < 30:  # 30 seconds cooldown
                                should_process = False
                        
                        if should_process:
                            plate_last_seen[plate_text] = current_time
                            unique_plates.add(plate_text)
                            all_detections.append(detection)
                            logger.info(f"Processing detection for plate: {plate_text}")
                    
                    # Collect parking updates from the result
                    for update in result.get('parking_updates', []):
                        parking_updates.append(update)
                
                frame_count += 1
                
            cap.release()
            
            if all_detections:
                self.stats['successful_detections'] += 1
            else:
                self.stats['failed_detections'] += 1
                
            return {
                'success': True,
                'detections': all_detections,
                'parking_updates': parking_updates,
                'total_frames_processed': frame_count // frame_interval,
                'unique_plates': len(unique_plates)
            }
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            self.stats['failed_detections'] += 1
            return {
                'success': False,
                'error': str(e),
                'detections': [],
                'parking_updates': []
            }
    
    def process_rtsp_stream(self, rtsp_url: str, duration: int = 60, update_parking: bool = True) -> Dict:
        """Process RTSP stream untuk deteksi plat nomor"""
        try:
            self.stats['total_processed'] += 1
            
            # Check if it's a YouTube URL and get the actual stream URL
            actual_stream_url = rtsp_url
            if self.is_youtube_url(rtsp_url):
                logger.info(f"Detected YouTube URL, extracting stream: {rtsp_url}")
                actual_stream_url = self.get_youtube_stream_url(rtsp_url)
                logger.info(f"Using extracted stream URL for processing")
            
            cap = cv2.VideoCapture(actual_stream_url)
            if not cap.isOpened():
                raise Exception(f"Cannot connect to stream: {rtsp_url}")
            
            logger.info(f"Successfully connected to stream, processing for {duration} seconds")
            logger.info(f"Stream processing will check frames every 2 seconds")
                
            start_time = time.time()
            all_detections = []
            unique_plates = set()
            parking_updates = []
            frame_count = 0
            plate_last_seen = {}  # Track when each plate was last processed
            
            # Process frames every 2 seconds for better detection
            last_process_time = 0
            
            while time.time() - start_time < duration:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame from stream")
                    time.sleep(1)
                    continue
                    
                current_time = time.time()
                if current_time - last_process_time >= 2:  # Process every 2 seconds
                    # Convert frame to bytes
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_data = buffer.tobytes()
                    
                    # Process frame with parking updates enabled
                    result = self.process_image_for_plates(image_data, update_parking)
                    
                    # Collect all detections and parking updates
                    for detection in result.get('detections', []):
                        plate_text = detection['plate_text']
                        if plate_text not in unique_plates:
                            unique_plates.add(plate_text)
                            all_detections.append(detection)
                    
                    # Collect parking updates from the result
                    for update in result.get('parking_updates', []):
                        parking_updates.append(update)
                    
                    last_process_time = current_time
                    
                frame_count += 1
                
            cap.release()
            
            # Log processing summary
            logger.info(f"Stream processing completed:")
            logger.info(f"  - Duration: {duration} seconds")
            logger.info(f"  - Total frames processed: {frame_count}")
            logger.info(f"  - Unique plates detected: {len(unique_plates)}")
            logger.info(f"  - Parking updates: {len(parking_updates)}")
            if unique_plates:
                logger.info(f"  - Detected plates: {', '.join(unique_plates)}")
            
            if all_detections:
                self.stats['successful_detections'] += 1
            else:
                self.stats['failed_detections'] += 1
                
            return {
                'success': True,
                'detections': all_detections,
                'parking_updates': parking_updates,
                'duration_processed': duration,
                'unique_plates': len(unique_plates),
                'total_frames': frame_count
            }
            
        except Exception as e:
            logger.error(f"Error processing RTSP stream: {e}")
            self.stats['failed_detections'] += 1
            return {
                'success': False,
                'error': str(e),
                'detections': [],
                'parking_updates': []
            }
    
    def handle_image_processing(self):
        """Handle image upload dan processing"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            update_parking = request.form.get('update_parking', 'true').lower() == 'true'
            
            # Read image data
            image_data = file.read()
            
            # Process image
            result = self.process_image_for_plates(image_data, update_parking)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error handling image processing: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_video_processing(self):
        """Handle video upload dan processing"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            update_parking = request.form.get('update_parking', 'true').lower() == 'true'
            
            # Save temporary file
            temp_dir = tempfile.gettempdir()
            filename = secure_filename(file.filename)
            temp_path = os.path.join(temp_dir, f"temp_{int(time.time())}_{filename}")
            
            file.save(temp_path)
            
            try:
                # Process video
                result = self.process_video_for_plates(temp_path, update_parking)
                return jsonify(result)
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"Error handling video processing: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_rtsp_processing(self):
        """Handle RTSP stream processing"""
        try:
            data = request.get_json()
            if not data or 'rtsp_url' not in data:
                return jsonify({'error': 'RTSP URL required'}), 400
                
            rtsp_url = data['rtsp_url']
            duration = data.get('duration', 60)
            update_parking = data.get('update_parking', True)
            
            # Process RTSP stream in background
            future = self.executor.submit(
                self.process_rtsp_stream, 
                rtsp_url, 
                duration, 
                update_parking
            )
            
            return jsonify({
                'message': 'RTSP processing started',
                'rtsp_url': rtsp_url,
                'duration': duration,
                'update_parking': update_parking
            })
            
        except Exception as e:
            logger.error(f"Error handling RTSP processing: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_integration_test(self):
        """Handle integration test"""
        try:
            # Create test image
            test_image = np.ones((300, 600, 3), dtype=np.uint8) * 255
            cv2.rectangle(test_image, (50, 100), (550, 200), (240, 240, 240), -1)
            cv2.rectangle(test_image, (50, 100), (550, 200), (0, 0, 0), 2)
            cv2.putText(test_image, 'B 1234 TEST', (150, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
            
            # Convert to bytes
            _, buffer = cv2.imencode('.jpg', test_image)
            image_data = buffer.tobytes()
            
            # Process test image with parking updates enabled
            result = self.process_image_for_plates(image_data, True)
            
            return jsonify({
                'test_status': 'completed',
                'result': result,
                'message': 'Integration test completed successfully'
            })
            
        except Exception as e:
            logger.error(f"Error in integration test: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_auto_exit_config(self):
        """Handle auto-exit configuration"""
        try:
            if request.method == 'GET':
                return jsonify({
                    'auto_exit_timeout_minutes': self.auto_exit_timeout_minutes,
                    'auto_exits_triggered': self.stats['auto_exits_triggered'],
                    'description': 'Vehicles detected after this timeout will be treated as exiting',
                    'status': 'enabled' if self.auto_exit_timeout_minutes > 0 else 'disabled'
                })
            
            elif request.method == 'POST':
                data = request.get_json()
                if not data or 'timeout_minutes' not in data:
                    return jsonify({'error': 'timeout_minutes required'}), 400
                
                new_timeout = int(data['timeout_minutes'])
                if new_timeout < 0:
                    return jsonify({'error': 'timeout_minutes must be >= 0'}), 400
                
                old_timeout = self.auto_exit_timeout_minutes
                self.auto_exit_timeout_minutes = new_timeout
                
                logger.info(f"Auto-exit timeout changed from {old_timeout} to {new_timeout} minutes")
                
                return jsonify({
                    'message': 'Auto-exit timeout updated successfully',
                    'old_timeout_minutes': old_timeout,
                    'new_timeout_minutes': new_timeout,
                    'status': 'enabled' if new_timeout > 0 else 'disabled'
                })
                
        except Exception as e:
            logger.error(f"Error handling auto-exit config: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_test_auto_exit(self):
        """Handle test auto-exit functionality"""
        try:
            data = request.get_json()
            if not data or 'plate_number' not in data:
                return jsonify({'error': 'plate_number required'}), 400
            
            plate_number = data['plate_number']
            action_type = data.get('action', 'test')  # 'test', 'clear', or 'determine'
            
            if action_type == 'clear':
                # Clear all Redis data for this plate
                last_detection_key = f"last_detection:{plate_number}"
                exit_status_key = f"exit_status:{plate_number}"
                self.redis_client.delete(last_detection_key)
                self.redis_client.delete(exit_status_key)
                
                return jsonify({
                    'test_status': 'completed',
                    'action': 'clear',
                    'plate_number': plate_number,
                    'message': f"Cleared all data for {plate_number}"
                })
            
            elif action_type == 'determine':
                # Just determine action based on current state
                action = self.determine_vehicle_action(plate_number)
                
                # If it's entry, update the detection time
                if action == 'entry':
                    self.update_last_detection_time(plate_number)
                
                return jsonify({
                    'test_status': 'completed',
                    'action': action,
                    'plate_number': plate_number,
                    'message': f"Vehicle {plate_number} determined as {action.upper()}"
                })
            
            else:  # Default 'test' action
                test_timeout = data.get('test_timeout_minutes', self.auto_exit_timeout_minutes)
                
                # Simulate old detection time
                old_time = datetime.now() - timedelta(minutes=test_timeout + 1)
                last_detection_key = f"last_detection:{plate_number}"
                self.redis_client.setex(last_detection_key, 86400, old_time.isoformat())
                
                # Test the logic
                action = self.determine_vehicle_action(plate_number)
                
                return jsonify({
                    'test_status': 'completed',
                    'plate_number': plate_number,
                    'simulated_last_detection': old_time.isoformat(),
                    'test_timeout_minutes': test_timeout,
                    'determined_action': action,
                    'expected_action': 'exit',
                    'test_passed': action == 'exit',
                    'message': f"Vehicle {plate_number} would be treated as {action.upper()}"
                })
            
        except Exception as e:
            logger.error(f"Error in auto-exit test: {e}")
            return jsonify({'error': str(e)}), 500
    
    def run(self, host='0.0.0.0', port=8004, debug=False):
        """Run the integration service"""
        logger.info(f"Starting SPARKA Integration Service on {host}:{port}")
        logger.info(f"Auto-exit timeout: {self.auto_exit_timeout_minutes} minutes")
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def main():
    service = SPARKAIntegrationService()
    
    # Run service
    port = int(os.getenv('PORT', 8004))
    service.run(port=port)

if __name__ == '__main__':
    main()