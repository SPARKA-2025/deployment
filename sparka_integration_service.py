#!/usr/bin/env python3
"""
SPARKA Integration Service - Optimized Version with Enhanced Logic
Optimizations:
1. Removed code duplication in plate processing logic
2. Improved Indonesian plate validation with better regex patterns
3. Consolidated detection processing into reusable functions
4. Enhanced error handling and logging
5. Reduced recursive API calls by caching detection results

Enhancements (Latest):
6. Improved determine_vehicle_action logic to consider active booking status
7. Added force_action parameter for manual testing
8. Enhanced logging with [ACTION_DETERMINATION] and [PARKING_UPDATE] tags
9. Better synchronization between frontend logic and backend grace period
10. Prioritizes entry when active booking is found, even within timeout period

Booking Logic Updates (v2.2):
11. All bookings (regular and special) complete after first successful entry (backend change)
12. Regular bookings: 1 hour timeout before expiry, complete after first entry
13. Special bookings: No timeout (expires 2099-12-31), complete after first entry
14. Grace period logic: 15 minutes for exit detection after any booking completion
15. Simplified action determination: active booking = entry, no booking + grace period = exit
16. Consistent behavior for all booking types, only timeout duration differs
"""

import os
import sys
import time
import json
import logging
import tempfile
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import redis
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizedSPARKAIntegrationService:
    """Optimized SPARKA Integration Service with reduced code duplication"""
    
    def __init__(self):
        # Service URLs - Use AI_API_URL from docker-compose environment

        self.ai_detection_url = os.getenv('AI_API_URL', 'http://localhost:5000') + '/predict'
        # Backend API URL - use host.docker.internal for Docker to access host machine
        self.backend_api_url = os.getenv('BACKEND_API_URL', 'http://host.docker.internal:8000')
        
        # Redis configuration - use localhost for local development, redis service name for Docker
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        try:
            # Parse Redis URL or use individual components
            if redis_url.startswith('redis://'):
                self.redis_client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=10)
            else:
                self.redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    db=int(os.getenv('REDIS_DB', 0)),
                    decode_responses=True,
                    socket_connect_timeout=10
                )
            # Test connection - Redis is mandatory for SPARKA Integration Service
            self.redis_client.ping()
            logger.info(f"Redis connection established using: {redis_url}")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            logger.error("Redis is required for SPARKA Integration Service to function properly")
            raise Exception(f"Redis connection required but failed: {e}")
        
        # Anti-looping configuration (prevent rapid entry-exit cycles)
        self.anti_looping_seconds = int(os.getenv('ANTI_LOOPING_SECONDS', 60))  # 60 seconds default
        
        # Booking validation configuration
        self.booking_active = os.getenv('BOOKING_ACTIVE', 'true').lower() == 'true'
        logger.info(f"Booking validation mode: {'ENABLED' if self.booking_active else 'DISABLED'}")
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful_detections': 0,
            'failed_detections': 0,
            'anti_looping_blocks': 0
        }
        
        # Thread pool for background processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Flask app setup
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Simplified configuration for optimized processing
        self.detection_timeout = 15  # Reduced timeout for faster processing
        
        logger.info("Optimized SPARKA Integration Service initialized")
    
    def handle_parking_stats(self):
        """Get parking statistics from backend API"""
        try:
            url = f"{self.backend_api_url}/api/ai/parking/stats"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                stats_data = response.json()
                return jsonify(stats_data)
            else:
                logger.error(f"Failed to get parking stats: {response.status_code}")
                return jsonify({'error': f'Backend API error: {response.status_code}'}), response.status_code
                
        except Exception as e:
            logger.error(f"Error getting parking stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_backend_health(self):
        """Check backend API health using /api/ai/health endpoint"""
        try:
            url = f"{self.backend_api_url}/api/ai/health"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                # Add integration service status
                health_data['integration_service'] = {
                    'status': 'healthy',
                    'version': '2.0-optimized',
                    'stats': self.stats
                }
                return jsonify(health_data)
            else:
                logger.error(f"Backend health check failed: {response.status_code}")
                return jsonify({
                    'status': 'unhealthy',
                    'backend_error': f'Backend API error: {response.status_code}',
                    'integration_service': {
                        'status': 'healthy',
                        'version': '2.0-optimized'
                    }
                }), 503
                
        except Exception as e:
            logger.error(f"Error checking backend health: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'integration_service': {
                    'status': 'healthy',
                    'version': '2.0-optimized'
                }
            }), 503
    
    def create_log_kendaraan(self, plate_number: str, action: str = None) -> Dict:
        """Create log kendaraan entry using /api/parking/update endpoint"""
        try:
            url = f"{self.backend_api_url}/api/parking/update"
            
            # Prepare payload based on action
            payload = {
                'plate_number': plate_number,
                'action': action or 'entry',
                'timestamp': datetime.now().isoformat(),
                'location': 'AI Detection System'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Log kendaraan created for {plate_number}: {result}")
                return {
                    'success': True,
                    'action': action,
                    'plate_number': plate_number,
                    'message': 'Log kendaraan berhasil dibuat',
                    'backend_response': result
                }
            else:
                logger.error(f"Failed to create log kendaraan for {plate_number}: {response.status_code}")
                return {
                    'success': False,
                    'action': action,
                    'plate_number': plate_number,
                    'error': f"Backend API error: {response.status_code}",
                    'message': 'Gagal membuat log kendaraan'
                }
                
        except Exception as e:
            logger.error(f"Error creating log kendaraan: {e}")
            return {
                'success': False,
                'action': action or 'unknown',
                'error': str(e),
                'message': f"Connection error: {str(e)}"
            }
    
    def handle_log_kendaraan(self):
        """Handle log kendaraan operations"""
        try:
            if request.method == 'GET':
                # Get log kendaraan data
                url = f"{self.backend_api_url}/api/ai/log-kendaraan"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    log_data = response.json()
                    return jsonify(log_data)
                else:
                    logger.error(f"Failed to get log kendaraan: {response.status_code}")
                    return jsonify({'error': f'Backend API error: {response.status_code}'}), response.status_code
            
            elif request.method == 'POST':
                # Create log kendaraan entry
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'JSON data required'}), 400
                
                url = f"{self.backend_api_url}/api/ai/log-kendaraan"
                response = requests.post(url, json=data, timeout=10)
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return jsonify(result)
                else:
                    logger.error(f"Failed to create log kendaraan: {response.status_code}")
                    return jsonify({'error': f'Backend API error: {response.status_code}'}), response.status_code
                    
        except Exception as e:
            logger.error(f"Error handling log kendaraan: {e}")
            return jsonify({'error': str(e)}), 500
    
    def setup_routes(self):
        """Setup Flask routes - optimized for /api/ai backend integration"""
        # Basic request logging
        @self.app.before_request
        def log_request_info():
            logger.info(f"Request: {request.method} {request.path}")
            
        @self.app.after_request
        def log_response_info(response):
            logger.info(f"Response: {request.method} {request.path} - {response.status_code}")
            return response
        
        # Core integration service routes
        self.app.route('/health', methods=['GET'])(self.handle_health)
        self.app.route('/process-image', methods=['POST'])(self.handle_image_processing)
        self.app.route('/process-video', methods=['POST'])(self.handle_video_processing)
        self.app.route('/process-rtsp', methods=['POST'])(self.handle_rtsp_processing)
        self.app.route('/process-cctv', methods=['POST'])(self.handle_rtsp_processing)  # Alias for CCTV
        self.app.route('/process-stream', methods=['POST'])(self.handle_rtsp_processing)  # Alias for streams
        self.app.route('/stats', methods=['GET'])(self.handle_stats)
        self.app.route('/test-integration', methods=['GET'])(self.handle_integration_test)
        self.app.route('/config/anti-looping', methods=['GET', 'POST'])(self.handle_anti_looping_config)
        self.app.route('/config/anti-looping/test', methods=['POST'])(self.handle_test_optimal_system)
        self.app.route('/test', methods=['GET', 'POST'])(self.handle_test_plate)
        
        logger.info("Routes registered: /test endpoint registered for GET and POST methods")
        print("Routes registered: /test endpoint registered for GET and POST methods", flush=True)
        
        # Direct proxy routes to backend /api/ai endpoints
        self.app.route('/api/parking/stats', methods=['GET'])(self.handle_parking_stats)
        self.app.route('/api/log-kendaraan', methods=['GET', 'POST'])(self.handle_log_kendaraan)
        self.app.route('/api/health', methods=['GET'])(self.handle_backend_health)
    
    def handle_health(self):
        """Local health check endpoint for integration service"""
        return jsonify({
            'status': 'healthy',
            'service': 'sparka-integration',
            'version': '2.0-optimized',
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'backend_endpoints': {
                'parking_update': '/api/ai/parking/update-status',
                'parking_stats': '/api/ai/parking/stats',
                'log_kendaraan': '/api/ai/log-kendaraan',
                'health': '/api/ai/health',
                'booking_check': '/api/booking/check/{plate_number}'
            }
        })
    
    def handle_stats(self):
        """Statistics endpoint"""
        return jsonify({
            'stats': self.stats,
            'anti_looping_seconds': self.anti_looping_seconds,
            'cache_size': len(self.detection_cache),
            'system_type': 'optimal_parking_system',
            'description': 'First detection = ENTRY, Second detection = EXIT'
        })
    
    def handle_test_plate(self):
        """Test endpoint untuk mengetes integrasi dengan backend menggunakan plat nomor langsung"""
        logger.info("Test endpoint called")
        try:
            # Get plate number and action from query parameter, JSON body, or form data
            if request.method == 'GET':
                plate_number = request.args.get('plate_number')
                force_action = request.args.get('action')  # Optional explicit action
            else:  # POST
                # Support both JSON and form-data
                if request.content_type and 'application/json' in request.content_type:
                    data = request.get_json() or {}
                    plate_number = data.get('plate_number')
                    force_action = data.get('action')  # Optional explicit action
                else:
                    # Form-data support
                    plate_number = request.form.get('plate_number')
                    force_action = request.form.get('action')  # Optional explicit action
                
                # Fallback to query parameter if not found in body/form
                if not plate_number:
                    plate_number = request.args.get('plate_number')
                if not force_action:
                    force_action = request.args.get('action')
            
            if not plate_number:
                return jsonify({
                    'success': False,
                    'error': 'Parameter plate_number diperlukan',
                    'usage': {
                        'GET': '/test?plate_number=B1234ABC&action=entry',
                        'POST': '/test dengan JSON body: {"plate_number": "B1234ABC", "action": "entry"}',
                        'note': 'Parameter action opsional (entry/exit). Jika tidak disediakan, sistem akan menentukan otomatis berdasarkan status booking dan riwayat deteksi.'
                    }
                }), 400
            
            # Validate action parameter if provided
            if force_action and force_action not in ['entry', 'exit']:
                return jsonify({
                    'success': False,
                    'error': 'Parameter action harus berupa "entry" atau "exit"',
                    'provided_action': force_action
                }), 400
            
            # Use original plate number without cleaning
            is_valid = self.validate_indonesian_plate(plate_number)
            
            # Check booking status first for better validation
            booking_status = self.check_booking_status(plate_number)
            has_active_booking = booking_status.get('has_booking', False)
            
            # Determine action with improved logic that considers booking status
            action = self.determine_vehicle_action(plate_number, force_action)
            
            # Enhanced validation for entry actions - Allow entry without booking but log warning
            if action == 'entry' and not has_active_booking:
                logger.warning(f"Test entry without booking for {plate_number}: Proceeding anyway (optimal system)")
                # Don't block entry in optimal system, just log the warning
            
            # Update parking status with determined action
            parking_result = self.update_parking_status(plate_number, action)
            
            # Create log kendaraan entry
            log_result = self.create_log_kendaraan(plate_number, action)
            
            # Update statistics
            self.stats['total_processed'] += 1
            if parking_result.get('success'):
                self.stats['successful_detections'] += 1
            else:
                self.stats['failed_detections'] += 1
            
            # Return enhanced test result
            return jsonify({
                'success': True,
                'plate_number': plate_number,
                'action': action,
                'parking_status': parking_result.get('success', False),
                'log_created': log_result.get('success', False),
                'message': parking_result.get('message', 'Test completed'),
                'booking_status': booking_status,
                'force_action_used': force_action is not None,
                'action_determination': {
                    'requested_action': force_action,
                    'determined_action': action,
                    'has_active_booking': has_active_booking,
                    'logic_applied': 'Improved logic with booking status consideration'
                },
                'endpoints_used': {
                    'booking_check': '/api/booking/check/{plate_number}',
                    'parking_update': '/api/ai/parking/update-status',
                    'log_kendaraan': '/api/parking/update'
                }
            })
            
        except Exception as e:
            logger.error(f"Error in test endpoint: {e}")
            self.stats['failed_detections'] += 1
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Terjadi kesalahan saat mengetes integrasi'
            }), 500
    
    def is_valid_plate(self, plate_text: str) -> bool:
        """Enhanced Indonesian plate validation with stricter rules"""
        if not plate_text or len(plate_text.strip()) < 5:
            return False
        
        # Clean and normalize
        cleaned = re.sub(r'[^A-Z0-9]', '', plate_text.upper().strip())
        
        # Indonesian plates: minimum 5 characters, maximum 9 characters
        if len(cleaned) < 5 or len(cleaned) > 9:
            return False
            
        has_letter = bool(re.search(r'[A-Z]', cleaned))
        has_number = bool(re.search(r'\d', cleaned))
        
        # Must have both letters and numbers
        if not (has_letter and has_number):
            return False
            
        # Indonesian plate pattern validation
        # Format: [A-Z]{1,2}[0-9]{1,4}[A-Z]{1,3}
        # Examples: B1234CD, S1336LF, H1962DQ
        pattern = r'^[A-Z]{1,2}\d{1,4}[A-Z]{1,3}$'
        if not re.match(pattern, cleaned):
            return False
            
        # Additional quality checks
        # Reject if too many repeated characters (OCR error)
        if len(set(cleaned)) < 3:
            return False
            
        # Reject obvious OCR errors and invalid patterns
        invalid_patterns = ['000', '111', '222', '333', '444', '555', '666', '777', '888', '999', 
                          'AAA', 'BBB', 'CCC', 'DDD', 'EEE', 'FFF', 'GGG', 'HHH', 'III', 'JJJ']
        for pattern in invalid_patterns:
            if pattern in cleaned:
                return False
                
        return True
    
    def calculate_plate_similarity(self, plate1: str, plate2: str) -> float:
        """Calculate similarity between two plate numbers using Levenshtein distance"""
        try:
            from difflib import SequenceMatcher
            
            # Clean both plates
            clean1 = re.sub(r'[^A-Z0-9]', '', plate1.upper().strip())
            clean2 = re.sub(r'[^A-Z0-9]', '', plate2.upper().strip())
            
            if not clean1 or not clean2:
                return 0.0
                
            # Calculate similarity ratio
            similarity = SequenceMatcher(None, clean1, clean2).ratio()
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating plate similarity: {e}")
            return 0.0
    
    def find_best_matching_plate(self, detected_plate: str, target_plates: list) -> dict:
        """Find the best matching plate from target plates based on similarity"""
        if not target_plates:
            return {'plate': detected_plate, 'similarity': 0.0, 'is_match': False}
            
        best_match = {'plate': detected_plate, 'similarity': 0.0, 'is_match': False}
        
        for target_plate in target_plates:
            similarity = self.calculate_plate_similarity(detected_plate, target_plate)
            
            if similarity > best_match['similarity']:
                best_match = {
                    'plate': target_plate,
                    'similarity': similarity,
                    'is_match': similarity >= 0.8  # 80% similarity threshold
                }
                
        return best_match
    
    def call_ai_detection(self, image_data: bytes, use_cache: bool = False) -> Dict:
        """Optimized AI detection call - no caching for real-time processing"""
        try:
            # Direct API call to sparka server /predict endpoint
            files = {'image': ('image.jpg', image_data, 'image/jpeg')}
            response = requests.post(self.ai_detection_url, files=files, timeout=15)
            
            if response.status_code == 200:
                api_result = response.json()
                
                # Handle API response format
                if isinstance(api_result, list):
                    detections = []
                    for prediction in api_result:
                        if isinstance(prediction, dict) and 'plate_number' in prediction:
                            plate_text = prediction.get('plate_number', '').strip()
                            confidence = prediction.get('confidence', 0.0)
                            
                            # Only include valid detections
                            if plate_text and plate_text not in ['No plate detected', 'No text detected']:
                                detections.append({
                                    'plate_text': plate_text,
                                    'confidence': confidence
                                })
                    
                    return {'detections': detections}
                else:
                    return api_result if isinstance(api_result, dict) else {'detections': []}
            else:
                logger.error(f"AI detection failed: {response.status_code}")
                return {'detections': []}
                
        except Exception as e:
            logger.error(f"Error calling AI detection: {e}")
            return {'detections': []}
    
    def should_process_detection(self, plate_number: str) -> bool:
        """Check if detection should be processed (anti-looping protection)
        
        Prevents rapid entry-exit cycles by enforcing minimum time between detections
        """
        try:
            anti_looping_key = f"anti_looping:{plate_number}"
            last_processed = self.redis_client.get(anti_looping_key)
            
            if last_processed:
                last_time = datetime.fromisoformat(last_processed)
                time_diff = datetime.now() - last_time
                
                if time_diff.total_seconds() < self.anti_looping_seconds:
                    self.stats['anti_looping_blocks'] += 1
                    logger.info(f"[ANTI_LOOPING] Plate {plate_number}: Blocked, {time_diff.total_seconds():.1f}s < {self.anti_looping_seconds}s")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking anti-looping for {plate_number}: {e}")
            return True  # Allow processing on error
    
    def update_anti_looping_timestamp(self, plate_number: str):
        """Update anti-looping timestamp in Redis"""
        try:
            key = f"anti_looping:{plate_number}"
            self.redis_client.setex(key, self.anti_looping_seconds * 2, datetime.now().isoformat())  # 2x TTL for safety
        except Exception as e:
            logger.error(f"Redis operation failed for anti-looping: {e}")
            raise e
    
    def update_last_detection_time(self, plate_number: str):
        """Update last detection time in Redis (legacy function, kept for compatibility)"""
        try:
            key = f"last_detection:{plate_number}"
            self.redis_client.setex(key, 86400, datetime.now().isoformat())  # 24 hours TTL
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            raise e
    
    def determine_vehicle_action(self, plate_number: str, force_action: Optional[str] = None) -> str:
        """Improved parking system: Considers booking status for better action determination
        
        Logic:
        1. If vehicle has active booking -> ENTRY (regardless of previous status)
        2. If vehicle has no booking but was recently inside -> EXIT
        3. Anti-looping protection for rapid detections
        4. Fallback to simple toggle logic if booking check fails
        """
        try:
            # If action is explicitly provided, use it (for manual testing)
            if force_action and force_action in ['entry', 'exit']:
                logger.info(f"[ACTION_DETERMINATION] Using forced action '{force_action}' for plate {plate_number}")
                return force_action
            
            # Check anti-looping protection first
            if not self.should_process_detection(plate_number):
                logger.info(f"[ACTION_DETERMINATION] Plate {plate_number}: Skipping due to anti-looping protection")
                return None  # Skip processing
            
            # Check booking status first - this is the key improvement
            booking_status = self.check_booking_status(plate_number)
            has_active_booking = booking_status.get('has_booking', False)
            
            last_detection_key = f"last_detection:{plate_number}"
            vehicle_status_key = f"vehicle_status:{plate_number}"  # 'inside' or 'outside'
            
            # Get current vehicle status
            vehicle_status = self.redis_client.get(vehicle_status_key) or 'outside'
            last_detection = self.redis_client.get(last_detection_key)
            
            current_time = datetime.now()
            
            # Booking validation logic based on BOOKING_ACTIVE setting
            if self.booking_active:
                # BOOKING_ACTIVE = true: Entry requires active booking
                if has_active_booking:
                    # Vehicle has active booking - prioritize ENTRY for new bookings
                    booking_details = booking_status.get('booking_details', {})
                    booking_type = booking_details.get('booking_type', 'unknown')
                    
                    # For active bookings, always ENTRY regardless of current status
                    # The booking completion will be handled by backend after successful entry
                    action = 'entry'
                    new_status = 'inside'
                    logger.info(f"[ACTION_DETERMINATION] Plate {plate_number}: Has active booking ({booking_type}) -> ENTRY")
                    logger.info(f"[ACTION_DETERMINATION] Booking details: {booking_details}")
                else:
                    # No active booking - check if vehicle was recently inside
                    if vehicle_status == 'inside':
                        # Vehicle was inside, this detection is EXIT
                        action = 'exit'
                        new_status = 'outside'
                        logger.info(f"[ACTION_DETERMINATION] Plate {plate_number}: No booking, was inside -> EXIT")
                    else:
                        # Vehicle was outside and no booking - DENY ENTRY when booking is required
                        logger.warning(f"[ACTION_DETERMINATION] Plate {plate_number}: ENTRY DENIED - No active booking (BOOKING_ACTIVE=true)")
                        return 'entry_denied'
            else:
                # BOOKING_ACTIVE = false: Entry allowed without booking
                if has_active_booking:
                    # Vehicle has active booking - prioritize ENTRY for new bookings
                    booking_details = booking_status.get('booking_details', {})
                    booking_type = booking_details.get('booking_type', 'unknown')
                    
                    action = 'entry'
                    new_status = 'inside'
                    logger.info(f"[ACTION_DETERMINATION] Plate {plate_number}: Has active booking ({booking_type}) -> ENTRY")
                    logger.info(f"[ACTION_DETERMINATION] Booking details: {booking_details}")
                else:
                    # No active booking - check if vehicle was recently inside
                    if vehicle_status == 'inside':
                        # Vehicle was inside, this detection is EXIT
                        action = 'exit'
                        new_status = 'outside'
                        logger.info(f"[ACTION_DETERMINATION] Plate {plate_number}: No booking, was inside -> EXIT")
                    else:
                        # Vehicle was outside and no booking - ALLOW ENTRY when booking is not required
                        action = 'entry'
                        new_status = 'inside'
                        logger.info(f"[ACTION_DETERMINATION] Plate {plate_number}: No booking, was outside -> ENTRY (BOOKING_ACTIVE=false)")
            
            # Update vehicle status and detection time
            self.redis_client.setex(vehicle_status_key, 86400, new_status)  # 24 hours TTL
            self.redis_client.setex(last_detection_key, 86400, current_time.isoformat())  # 24 hours TTL
            
            # Update anti-looping timestamp
            self.update_anti_looping_timestamp(plate_number)
            
            logger.info(f"[ACTION_DETERMINATION] Plate {plate_number}: {action.upper()} determined, status: {vehicle_status} -> {new_status}, booking: {has_active_booking}")
            return action
                
        except Exception as e:
            logger.error(f"[ACTION_DETERMINATION] Error determining vehicle action for {plate_number}: {e}")
            return 'entry'  # Default to entry on error
    
    def reset_vehicle_status_for_new_booking(self, plate_number: str) -> None:
        """Reset vehicle status to 'outside' for new bookings to ensure proper entry detection"""
        try:
            vehicle_status_key = f"vehicle_status:{plate_number}"
            # Force reset to 'outside' for new bookings
            self.redis_client.setex(vehicle_status_key, 86400, 'outside')
            logger.info(f"[BOOKING_RESET] Vehicle status reset to 'outside' for {plate_number} (new booking)")
        except Exception as e:
            logger.error(f"[BOOKING_RESET] Error resetting vehicle status for {plate_number}: {e}")
    
    def check_booking_status(self, plate_number: str) -> Dict:
        """Check if vehicle has valid booking via backend API - using /api/booking/check/{plate_number}"""
        try:
            # Use the dedicated booking check endpoint
            url = f"{self.backend_api_url}/api/booking/check/{plate_number}"
            print(f"Checking booking status for {plate_number} at URL: {url}")
            logger.info(f"Checking booking status for {plate_number} at URL: {url}")
            sys.stdout.flush()
            
            response = requests.get(url, timeout=10)
            print(f"Booking API response status: {response.status_code}")
            print(f"Booking API response text: {response.text}")
            logger.info(f"Booking API response status: {response.status_code}")
            logger.info(f"Booking API response text: {response.text}")
            sys.stdout.flush()
            
            if response.status_code == 200:
                booking_data = response.json()
                logger.info(f"Booking check result for {plate_number}: {booking_data}")
                sys.stdout.flush()
                
                has_booking = booking_data.get('has_booking', False)
                booking_details = booking_data.get('booking_details', {})
                
                # Check if this is a new booking (recently created)
                if has_booking and booking_details:
                    booking_time_str = booking_details.get('booking_time', '')
                    if booking_time_str:
                        try:
                            # Parse booking time
                            booking_time = datetime.fromisoformat(booking_time_str.replace('Z', '+00:00'))
                            current_time = datetime.now()
                            
                            # If booking was created within last 5 minutes, consider it new
                            time_diff = (current_time - booking_time.replace(tzinfo=None)).total_seconds()
                            if time_diff < 300:  # 5 minutes
                                logger.info(f"[BOOKING_CHECK] New booking detected for {plate_number} (created {time_diff:.0f}s ago)")
                                # Reset vehicle status for new bookings
                                self.reset_vehicle_status_for_new_booking(plate_number)
                        except Exception as e:
                            logger.warning(f"[BOOKING_CHECK] Could not parse booking time for {plate_number}: {e}")
                
                return {
                    'has_booking': has_booking,
                    'booking_details': booking_details
                }
            else:
                logger.warning(f"Booking check failed for {plate_number}: {response.status_code} - {response.text}")
                sys.stdout.flush()
                return {'has_booking': False, 'error': f"API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error checking booking status for {plate_number}: {e}")
            sys.stdout.flush()
            return {'has_booking': False, 'error': str(e)}
    
    def update_parking_status(self, plate_number: str, action: Optional[str] = None) -> Dict:
        """Update parking status via backend API using /api/ai/parking/update-status"""
        try:
            # Determine action if not provided using improved logic
            if action is None:
                action = self.determine_vehicle_action(plate_number)
                if action is None:
                    # Anti-looping protection triggered
                    logger.info(f"[PARKING_UPDATE] Skipping update for {plate_number}: Anti-looping protection")
                    return {
                        'success': False,
                        'action': 'skipped',
                        'plate_number': plate_number,
                        'message': 'Detection skipped due to anti-looping protection',
                        'reason': 'anti_looping'
                    }
                logger.info(f"[PARKING_UPDATE] Action determined for {plate_number}: {action}")
            else:
                logger.info(f"[PARKING_UPDATE] Using provided action for {plate_number}: {action}")
            
            # Handle entry_denied action
            if action == 'entry_denied':
                logger.warning(f"[PARKING_UPDATE] Entry denied for {plate_number}: No active booking (BOOKING_ACTIVE=true)")
                return {
                    'success': False,
                    'action': 'entry_denied',
                    'plate_number': plate_number,
                    'message': 'Entry denied: Active booking required',
                    'reason': 'no_booking_required'
                }
            
            # For entry, handle booking validation based on BOOKING_ACTIVE setting
            if action == 'entry':
                if self.booking_active:
                    # BOOKING_ACTIVE = true: Validate booking is required
                    booking_status = self.check_booking_status(plate_number)
                    if not booking_status.get('has_booking', False):
                        logger.warning(f"[PARKING_UPDATE] Entry denied for {plate_number}: No active booking (BOOKING_ACTIVE=true)")
                        return {
                            'success': False,
                            'action': 'entry_denied',
                            'plate_number': plate_number,
                            'message': 'Entry denied: Active booking required',
                            'reason': 'no_booking_required'
                        }
                    else:
                        logger.info(f"[PARKING_UPDATE] Entry allowed for {plate_number}: Active booking found")
                else:
                    # BOOKING_ACTIVE = false: Entry allowed without booking
                    logger.info(f"[PARKING_UPDATE] Entry allowed for {plate_number}: Booking validation disabled")
                
                # Update detection time for successful entry
                self.update_last_detection_time(plate_number)
                logger.info(f"[PARKING_UPDATE] Detection time updated for {plate_number} entry")
                
            elif action == 'exit':
                # No special handling needed for exit
                logger.info(f"[PARKING_UPDATE] Processing exit for {plate_number}")
            
            # Call backend API to update parking status using the new /api/ai/parking/update-status endpoint
            url = f"{self.backend_api_url}/api/ai/parking/update-status"
            payload = {
                'plat_nomor': plate_number,
                'action': action,
                'confidence': 0.95,  # Default confidence for AI detection
                'detection_time': datetime.now().isoformat(),
                'location': 'AI Detection System',
                'camera_id': 'sparka_integration_service'
            }
            
            logger.info(f"[PARKING_UPDATE] Calling backend API for {plate_number} {action}: {url}")
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:  # Accept both 200 OK and 201 Created
                result = response.json()
                logger.info(f"[PARKING_UPDATE] SUCCESS - Parking {action} recorded for {plate_number}: {result}")
                return {
                    'success': True,
                    'action': action,
                    'plate_number': plate_number,
                    'message': f'Parking {action} berhasil dicatat',
                    'backend_response': result
                }
            else:
                logger.error(f"[PARKING_UPDATE] FAILED - Backend API error for {plate_number}: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'action': action,
                    'plate_number': plate_number,
                    'error': f"Backend API error: {response.status_code}",
                    'message': f'Gagal mencatat parking {action}'
                }
                
        except Exception as e:
            logger.error(f"[PARKING_UPDATE] EXCEPTION - Error updating parking status for {plate_number}: {e}")
            return {
                'success': False,
                'action': action or 'unknown',
                'error': str(e),
                'message': f"Connection error: {str(e)}"
            }
    
    def process_detections(self, detections: List[Dict], update_parking: bool = True) -> Tuple[List[Dict], List[Dict]]:
        """Simplified detection processing for better performance"""
        processed_detections = []
        parking_updates = []
        
        for detection in detections:
            plate_text = detection.get('plate_text', '').strip()
            confidence = detection.get('confidence', 0)
            
            # Quick validation
            if plate_text and confidence > 0.7 and self.is_valid_plate(plate_text):
                processed_detections.append({
                    'plate_text': plate_text,
                    'confidence': confidence
                })
                
                # Update parking if enabled
                if update_parking:
                    action = self.determine_vehicle_action(plate_text)
                    if action:
                        update_result = self.update_parking_status(plate_text, action)
                        parking_updates.append({
                            'plate_number': plate_text,
                            'action': action,
                            'success': update_result.get('success', False)
                        })
        
        return processed_detections, parking_updates
    
    def process_image_for_plates(self, image_data: bytes, update_parking: bool = True) -> Dict:
        """Process image untuk deteksi plat nomor - optimized version"""
        try:
            self.stats['total_processed'] += 1
            
            # Call AI detection with caching
            detection_result = self.call_ai_detection(image_data, use_cache=True)
            detections = detection_result.get('detections', [])
            
            # Process detections using consolidated logic
            processed_detections, parking_updates = self.process_detections(detections, update_parking)
            
            if processed_detections:
                self.stats['successful_detections'] += 1
            else:
                self.stats['failed_detections'] += 1
                
            return {
                'success': True,
                'detections': processed_detections,
                'parking_updates': parking_updates,
                'total_detections': len(processed_detections),
                'cached': detection_result.get('cached', False)
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
    
    def process_video_for_plates(self, video_source: str, update_parking: bool = True, duration: int = None) -> Dict:
        """Optimized video processing for plate detection - 5 FPS fixed"""
        try:
            self.stats['total_processed'] += 1
            start_time = time.time()
            
            cap = cv2.VideoCapture(video_source)
            if not cap.isOpened():
                raise Exception(f"Cannot open video source: {video_source}")
                
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
            # Optimized 3 FPS processing for faster processing
            frame_interval = max(1, fps // 3)
            
            all_detections = []
            unique_plates = set()
            parking_updates = []
            plate_cooldown = {}  # Simple cooldown tracking
            plate_confidence_tracker = {}  # Track highest confidence for each plate
            
            # Target plates for matching (expected plates)
            #target_plates = ['S1336LF', 'H1962DQ']  # Known valid plates
            
            frame_count = 0
            processed_frames = 0
            
            logger.info(f"Processing video at 3 FPS (every {frame_interval} frames) for faster processing")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Process every Nth frame for 5 FPS
                if frame_count % frame_interval == 0:
                    current_time = time.time()
                    
                    # Convert frame to bytes
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    image_data = buffer.tobytes()
                    
                    # Direct AI detection call (no preprocessing needed)
                    detection_result = self.call_ai_detection(image_data, use_cache=False)
                    detections = detection_result.get('detections', [])
                    
                    # Process detections with enhanced validation and matching
                    for detection in detections:
                        plate_text = detection.get('plate_text', '').strip()
                        confidence = detection.get('confidence', 0.0)
                        
                        # Skip empty/invalid detections
                        if not plate_text or plate_text in ['No plate detected', 'No text detected']:
                            continue
                        
                        # Apply confidence threshold (0.0 for debugging - AI returns 0.0)
                        if confidence < 0.0:
                            logger.debug(f"Low confidence detection rejected: {plate_text} (confidence: {confidence:.2f})")
                            continue
                        
                        # Enhanced plate validation with stricter rules
                        if not self.is_valid_plate(plate_text):
                            logger.debug(f"Invalid plate format rejected: {plate_text}")
                            continue
                        
                        # Use plate text as-is without target plate matching
                        final_plate = plate_text
                        similarity = 1.0
                        
                        # Track confidence for each plate (keep highest)
                        if final_plate not in plate_confidence_tracker or confidence > plate_confidence_tracker[final_plate]['confidence']:
                            plate_confidence_tracker[final_plate] = {
                                'confidence': confidence,
                                'similarity': similarity,
                                'original_text': plate_text,
                                'frame': frame_count
                            }
                        
                        # Cooldown check (reduced to 15 seconds for faster processing)
                        if final_plate in plate_cooldown:
                            if current_time - plate_cooldown[final_plate] < 15:
                                continue
                        
                        # Check booking status before processing
                        booking_status = self.check_booking_status(final_plate)
                        has_booking = booking_status.get('has_booking', False)
                        
                        # Strict booking validation - reject entry if no booking
                        action = self.determine_vehicle_action(final_plate)
                        if action == 'entry' and not has_booking:
                            logger.warning(f"Entry denied for {final_plate}: No active booking found")
                            parking_updates.append({
                                'plate_number': final_plate,
                                'action': 'entry_denied',
                                'success': False
                            })
                            continue
                        
                        # Process valid detection
                        plate_cooldown[final_plate] = current_time
                        unique_plates.add(final_plate)
                        
                        # Update parking status
                        if action and update_parking:
                            update_result = self.update_parking_status(final_plate, action)
                            parking_updates.append({
                                'plate_number': final_plate,
                                'action': action,
                                'success': update_result.get('success', False)
                            })
                            
                        all_detections.append({
                            'plate_text': final_plate,
                            'action': action
                        })
                    
                    processed_frames += 1
                
                frame_count += 1
                
            cap.release()
            processing_time = time.time() - start_time
            
            # Generate optimization summary
            optimization_summary = {
                'frame_rate_optimization': f"Processed at 3 FPS (every {frame_interval} frames) instead of full {fps} FPS",
                'time_saved': f"Estimated {((fps/3) - 1) * 100:.0f}% faster processing",
                'plate_matching': "Applied plate validation and cleaning",
                'booking_validation': "Strict booking validation - entry denied without active booking",
                'confidence_tracking': f"Tracked highest confidence for {len(plate_confidence_tracker)} unique plates",
                'cooldown_optimization': "Reduced cooldown to 15 seconds for faster processing"
            }
            
            logger.info(f"Video processed: {processed_frames} frames in {processing_time:.2f}s, {len(unique_plates)} unique plates")
            logger.info(f"Optimization applied: 3 FPS processing, plate matching, strict booking validation")
            
            # Log plate confidence summary
            for plate, info in plate_confidence_tracker.items():
                logger.info(f"Plate {plate}: confidence={info['confidence']:.2f}, similarity={info['similarity']:.2f}, frame={info['frame']}")
            
            if all_detections:
                self.stats['successful_detections'] += 1
            else:
                self.stats['failed_detections'] += 1
                
            return {
                'success': True,
                'detections': all_detections,
                'parking_updates': parking_updates
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
        """Simplified RTSP stream processing"""
        # Use the same optimized video processing logic
        return self.process_video_for_plates(rtsp_url, update_parking, duration)
    
    def handle_image_processing(self):
        """Handle image upload dan processing"""
        try:
            # Check for both 'file' and 'image' parameters
            file = None
            if 'file' in request.files:
                file = request.files['file']
            elif 'image' in request.files:
                file = request.files['image']
            
            if file is None:
                return jsonify({'error': 'No file provided'}), 400
                
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
        """Handle video processing - supports file upload, video URLs, and local file paths"""
        try:
            # Check for JSON data with video_path or video_url
            data = request.get_json() if request.is_json else None
            if data:
                video_source = data.get('video_path') or data.get('video_url')
                if video_source:
                    update_parking = data.get('update_parking', True)
                    duration = data.get('duration', None)
                    
                    # Check if it's a local file path
                    if os.path.exists(video_source):
                        logger.info(f"Processing local video file: {video_source}")
                    else:
                        logger.info(f"Processing video URL/stream: {video_source}")
                    
                    # Process video using unified method
                    result = self.process_video_for_plates(video_source, update_parking, duration)
                    return jsonify(result)
            
            # Check for file upload
            file = None
            if 'file' in request.files:
                file = request.files['file']
            elif 'video' in request.files:
                file = request.files['video']
            elif 'image' in request.files:
                file = request.files['image']
            
            if file is None:
                return jsonify({
                    'error': 'No file, video_path, or video_url provided',
                    'usage': {
                        'local_file': 'POST with JSON: {"video_path": "C:/path/to/video.mp4"}',
                        'file_upload': 'POST with multipart form-data and file field',
                        'stream_url': 'POST with JSON: {"video_url": "http://stream.url"}'
                    }
                }), 400
                
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            update_parking = request.form.get('update_parking', 'true').lower() == 'true'
            duration = request.form.get('duration')
            duration = int(duration) if duration else None
            
            # Save temporary file
            temp_dir = tempfile.gettempdir()
            filename = secure_filename(file.filename)
            temp_path = os.path.join(temp_dir, f"temp_{int(time.time())}_{filename}")
            
            file.save(temp_path)
            
            try:
                result = self.process_video_for_plates(temp_path, update_parking, duration)
                return jsonify(result)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"Error handling video processing: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_rtsp_processing(self):
        """Handle RTSP/CCTV stream processing - unified with video processing"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON data required'}), 400
            
            # Support multiple URL parameter names
            stream_url = data.get('rtsp_url') or data.get('cctv_url') or data.get('stream_url') or data.get('video_url')
            if not stream_url:
                return jsonify({'error': 'Stream URL required (rtsp_url, cctv_url, stream_url, or video_url)'}), 400
                
            duration = data.get('duration', 60)
            update_parking = data.get('update_parking', True)
            async_processing = data.get('async', True)  # Default to async processing
            
            if async_processing:
                # Process stream in background
                future = self.executor.submit(
                    self.process_video_for_plates,  # Use unified video processing
                    stream_url, 
                    update_parking,
                    duration
                )
                
                return jsonify({
                    'message': 'Stream processing started in background',
                    'stream_url': stream_url,
                    'duration': duration,
                    'update_parking': update_parking,
                    'async': True
                })
            else:
                # Process synchronously
                result = self.process_video_for_plates(stream_url, update_parking, duration)
                return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error handling stream processing: {e}")
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
                'message': 'Integration test completed successfully',
                'optimizations': {
                    'caching_enabled': True,
                    'consolidated_processing': True,
                    'enhanced_validation': True
                }
            })
            
        except Exception as e:
            logger.error(f"Error in integration test: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_anti_looping_config(self):
        """Handle anti-looping configuration"""
        try:
            if request.method == 'GET':
                return jsonify({
                    'anti_looping_seconds': self.anti_looping_seconds,
                    'anti_looping_blocks': self.stats['anti_looping_blocks'],
                    'description': 'Minimum seconds between detections to prevent rapid entry-exit cycles',
                    'status': 'enabled' if self.anti_looping_seconds > 0 else 'disabled',
                    'system_type': 'optimal_parking_system'
                })
            
            elif request.method == 'POST':
                data = request.get_json()
                if not data or 'anti_looping_seconds' not in data:
                    return jsonify({'error': 'anti_looping_seconds required'}), 400
                
                new_timeout = int(data['anti_looping_seconds'])
                if new_timeout < 0:
                    return jsonify({'error': 'anti_looping_seconds must be >= 0'}), 400
                
                old_timeout = self.anti_looping_seconds
                self.anti_looping_seconds = new_timeout
                
                logger.info(f"Anti-looping timeout changed from {old_timeout} to {new_timeout} seconds")
                
                return jsonify({
                    'message': 'Anti-looping timeout updated successfully',
                    'old_anti_looping_seconds': old_timeout,
                    'new_anti_looping_seconds': new_timeout,
                    'status': 'enabled' if new_timeout > 0 else 'disabled'
                })
                
        except Exception as e:
            logger.error(f"Error handling anti-looping config: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_test_optimal_system(self):
        """Handle test optimal parking system functionality"""
        try:
            data = request.get_json()
            if not data or 'plate_number' not in data:
                return jsonify({'error': 'plate_number required'}), 400
            
            plate_number = data['plate_number']
            action_type = data.get('action', 'determine')  # 'clear', 'determine', or 'status'
            
            if action_type == 'clear':
                # Clear all Redis data for this plate
                try:
                    last_detection_key = f"last_detection:{plate_number}"
                    vehicle_status_key = f"vehicle_status:{plate_number}"
                    anti_looping_key = f"anti_looping:{plate_number}"
                    self.redis_client.delete(last_detection_key)
                    self.redis_client.delete(vehicle_status_key)
                    self.redis_client.delete(anti_looping_key)
                    message = f"Cleared all data for {plate_number}"
                except Exception as e:
                    message = f"Failed to clear data for {plate_number}: {e}"
                
                return jsonify({
                    'test_status': 'completed',
                    'action': 'clear',
                    'plate_number': plate_number,
                    'message': message
                })
            
            elif action_type == 'status':
                # Get current status without changing anything
                try:
                    vehicle_status_key = f"vehicle_status:{plate_number}"
                    last_detection_key = f"last_detection:{plate_number}"
                    anti_looping_key = f"anti_looping:{plate_number}"
                    
                    vehicle_status = self.redis_client.get(vehicle_status_key) or 'outside'
                    last_detection = self.redis_client.get(last_detection_key)
                    anti_looping = self.redis_client.get(anti_looping_key)
                    
                    return jsonify({
                        'test_status': 'completed',
                        'action': 'status',
                        'plate_number': plate_number,
                        'vehicle_status': vehicle_status,
                        'last_detection': last_detection,
                        'anti_looping_until': anti_looping,
                        'next_action': 'entry' if vehicle_status == 'outside' else 'exit'
                    })
                except Exception as e:
                    return jsonify({
                        'test_status': 'failed',
                        'plate_number': plate_number,
                        'error': str(e)
                    })
            
            else:  # Default 'determine' action
                # Determine action based on current state
                action = self.determine_vehicle_action(plate_number)
                
                return jsonify({
                    'test_status': 'completed',
                    'action': action or 'blocked',
                    'plate_number': plate_number,
                    'message': f"Vehicle {plate_number} determined as {(action or 'BLOCKED').upper()}",
                    'system_type': 'optimal_parking_system'
                })
            
        except Exception as e:
            logger.error(f"Error in optimal system test: {e}")
            return jsonify({'error': str(e)}), 500
    
    def run(self, host='0.0.0.0', port=8030, debug=False):
        """Run the integration service"""
        # Enable werkzeug logging
        import logging
        logging.getLogger('werkzeug').setLevel(logging.INFO)
        
        logger.info(f"Starting Optimized SPARKA Integration Service on {host}:{port}")
        logger.info(f"System Type: Optimal Parking System (First detection = ENTRY, Second detection = EXIT)")
        logger.info(f"Anti-looping protection: {self.anti_looping_seconds} seconds")
        logger.info(f"Frame processing: 3 FPS with confidence threshold 0.3 (optimized)")
        logger.info(f"Optimizations: No caching, adaptive validation, simplified processing")
        
        # Enable debug mode to see more detailed logs
        self.app.run(host=host, port=port, debug=True, threaded=True)

def main():
    service = OptimizedSPARKAIntegrationService()
    
    # Run service
    port = int(os.getenv('PORT', 8030))
    service.run(port=port)

if __name__ == '__main__':
    main()