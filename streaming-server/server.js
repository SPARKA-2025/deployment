const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const fs = require('fs-extra');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const redis = require('redis');

const app = express();
const PORT = process.env.PORT || 8010;

// Middleware
app.use(cors());
app.use(express.json());
app.use('/hls', express.static(path.join(__dirname, 'public/hls')));

// Redis client setup with fallback
let redisClient = null;
let redisAvailable = false;

async function initializeRedis() {
    try {
        const redisHost = process.env.REDIS_HOST || 'localhost';
        const redisPort = process.env.REDIS_PORT || 6379;
        const redisUrl = `redis://${redisHost}:${redisPort}`;
        
        redisClient = redis.createClient({
            url: redisUrl,
            socket: {
                connectTimeout: 5000,
                reconnectStrategy: false // Disable auto-reconnect to prevent spam
            }
        });

        redisClient.on('error', (err) => {
            if (!redisAvailable) {
                console.warn('⚠️  Redis not available, using memory storage as fallback');
                redisAvailable = false;
                redisClient = null;
            }
        });

        redisClient.on('connect', () => {
            console.log('✅ Redis connected successfully');
            redisAvailable = true;
        });

        // Try to connect to Redis with timeout
        const connectPromise = redisClient.connect();
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Connection timeout')), 3000)
        );
        
        await Promise.race([connectPromise, timeoutPromise]).catch((err) => {
            console.warn('⚠️  Redis connection failed, using memory storage');
            redisAvailable = false;
            redisClient = null;
        });
    } catch (error) {
        console.warn('⚠️  Redis setup failed, using memory storage');
        redisAvailable = false;
        redisClient = null;
    }
}

// In-memory storage as fallback
const memoryStorage = {
    cache: new Map(),
    
    async setEx(key, ttl, value) {
        this.cache.set(key, { value, expiry: Date.now() + (ttl * 1000) });
    },
    
    async get(key) {
        const item = this.cache.get(key);
        if (item && item.expiry > Date.now()) {
            return item.value;
        }
        if (item) {
            this.cache.delete(key);
        }
        return null;
    },
    
    async del(key) {
        this.cache.delete(key);
    }
};

// Storage helper functions
const storage = {
    async setEx(key, ttl, value) {
        if (redisAvailable && redisClient) {
            return await redisClient.setEx(key, ttl, value);
        } else {
            return await memoryStorage.setEx(key, ttl, value);
        }
    },
    
    async get(key) {
        if (redisAvailable && redisClient) {
            return await redisClient.get(key);
        } else {
            return await memoryStorage.get(key);
        }
    },
    
    async del(key) {
        if (redisAvailable && redisClient) {
            return await redisClient.del(key);
        } else {
            return await memoryStorage.del(key);
        }
    }
};

// Initialize Redis connection
initializeRedis().then(() => {
    console.log(`Storage backend: ${redisAvailable ? 'Redis' : 'Memory (fallback)'}`);
});

// Store active streams
const activeStreams = new Map();

// Ensure directories exist
fs.ensureDirSync(path.join(__dirname, 'public/hls'));
fs.ensureDirSync(path.join(__dirname, 'streams'));

// Helper functions

/**
 * Detect stream type from URL
 * @param {string} url - Stream URL
 * @returns {string} Stream type
 */
function detectStreamType(url) {
    const lowerUrl = url.toLowerCase();
    
    if (lowerUrl.startsWith('rtsp://')) {
        return 'rtsp';
    } else if (lowerUrl.includes('youtube.com') || lowerUrl.includes('youtu.be')) {
        return 'youtube';
    } else if (lowerUrl.includes('.m3u8')) {
        return 'hls';
    } else if (lowerUrl.includes('.mp4')) {
        return 'mp4';
    } else if (lowerUrl.startsWith('http://') || lowerUrl.startsWith('https://')) {
        return 'http';
    }
    
    return 'unknown';
}

/**
 * Convert RTSP stream to HLS format
 * @param {string} sourceUrl - RTSP stream URL
 * @param {string} streamId - Unique stream identifier
 * @returns {Promise<string>} HLS URL
 */
function convertToHls(sourceUrl, streamId) {
    return new Promise((resolve, reject) => {
        const outputDir = path.join(__dirname, 'public/hls', streamId);
        fs.ensureDirSync(outputDir);
        
        const playlistPath = path.join(outputDir, 'index.m3u8');
        const segmentPattern = path.join(outputDir, 'segment_%03d.ts');
        
        // Verify this is an RTSP stream
        const streamType = detectStreamType(sourceUrl);
        if (streamType !== 'rtsp') {
            reject(new Error(`Only RTSP streams are supported for conversion. Received: ${streamType}`));
            return;
        }
        
        // Set FFmpeg arguments for RTSP to HLS conversion
        const ffmpegArgs = [
            '-i', sourceUrl,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-f', 'hls',
            '-hls_time', '2',
            '-hls_list_size', '10',
            '-hls_flags', 'delete_segments',
            '-hls_segment_filename', segmentPattern,
            playlistPath
        ];
        
        console.log(`Starting FFmpeg conversion for stream ${streamId}`);
        console.log(`Source URL: ${sourceUrl} (Type: ${streamType})`);
        console.log(`Output: ${playlistPath}`);
        
        const ffmpeg = spawn('ffmpeg', ffmpegArgs);
        
        ffmpeg.stderr.on('data', (data) => {
            console.log(`FFmpeg ${streamId}: ${data}`);
        });
        
        ffmpeg.on('error', (error) => {
            console.error(`FFmpeg error for stream ${streamId}:`, error);
            reject(error);
        });
        
        // Wait for playlist file to be created
        const checkPlaylist = setInterval(() => {
            if (fs.existsSync(playlistPath)) {
                clearInterval(checkPlaylist);
                const hlsUrl = `/hls/${streamId}/index.m3u8`;
                console.log(`HLS stream ready: ${hlsUrl}`);
                resolve(hlsUrl);
            }
        }, 1000);
        
        // Store stream info
        activeStreams.set(streamId, {
            sourceUrl,
            streamType,
            ffmpegProcess: ffmpeg,
            hlsUrl: `/hls/${streamId}/index.m3u8`,
            startTime: new Date(),
            outputDir
        });
        
        // Handle process exit
        ffmpeg.on('close', (code) => {
            console.log(`FFmpeg process for stream ${streamId} exited with code ${code}`);
            activeStreams.delete(streamId);
            // Clean up files
            fs.removeSync(outputDir);
        });
    });
}

/**
 * Stop streaming and cleanup
 * @param {string} streamId - Stream identifier
 */
function stopStream(streamId) {
    const stream = activeStreams.get(streamId);
    if (stream) {
        console.log(`Stopping stream ${streamId}`);
        stream.ffmpegProcess.kill('SIGTERM');
        activeStreams.delete(streamId);
        
        // Clean up files
        setTimeout(() => {
            if (fs.existsSync(stream.outputDir)) {
                fs.removeSync(stream.outputDir);
            }
        }, 5000);
        
        return true;
    }
    return false;
}

// API Routes

/**
 * Start RTSP to HLS conversion
 * POST /api/stream/start
 * Body: { sourceUrl: string, cctvId?: string, streamType?: string }
 */
app.post('/api/stream/start', async (req, res) => {
    try {
        const { sourceUrl, rtspUrl, cctvId, streamType } = req.body;
        
        // Support both old 'rtspUrl' and new 'sourceUrl' parameter names for backward compatibility
        const streamUrl = sourceUrl || rtspUrl;
        
        if (!streamUrl) {
            return res.status(400).json({ error: 'Stream URL is required' });
        }
        
        // Detect stream type
        const detectedStreamType = detectStreamType(streamUrl);
        console.log(`Received request to start stream: ${streamUrl} (Type: ${detectedStreamType})`);
        
        // Only process RTSP streams - reject others
        if (detectedStreamType !== 'rtsp') {
            return res.status(400).json({ 
                error: 'Only RTSP streams are supported for conversion',
                streamType: detectedStreamType,
                sourceUrl: streamUrl,
                message: 'Non-RTSP streams should be used directly without conversion'
            });
        }
        
        // Generate unique stream ID
        const streamId = cctvId || uuidv4();
        
        // Check if stream already exists
        if (activeStreams.has(streamId)) {
            const existingStream = activeStreams.get(streamId);
            return res.json({
                success: true,
                streamId,
                hlsUrl: existingStream.hlsUrl,
                streamType: existingStream.streamType,
                message: 'RTSP stream already converted and active'
            });
        }
        
        // Start RTSP to HLS conversion
        const hlsUrl = await convertToHls(streamUrl, streamId);
        
        // Cache stream info
        await storage.setEx(`stream:${streamId}`, 3600, JSON.stringify({
            sourceUrl: streamUrl,
            streamType: detectedStreamType,
            hlsUrl,
            startTime: new Date().toISOString()
        }));
        
        res.json({
            success: true,
            streamId,
            hlsUrl,
            streamType: detectedStreamType,
            sourceUrl: streamUrl,
            message: 'RTSP stream converted to HLS successfully'
        });
        
    } catch (error) {
        console.error('Error converting RTSP stream:', error);
        res.status(500).json({ 
            error: 'Failed to convert RTSP stream',
            details: error.message 
        });
    }
});

/**
 * Stop streaming
 * POST /api/stream/stop
 * Body: { streamId: string }
 */
app.post('/api/stream/stop', async (req, res) => {
    try {
        const { streamId } = req.body;
        
        if (!streamId) {
            return res.status(400).json({ error: 'Stream ID is required' });
        }
        
        const stopped = stopStream(streamId);
        
        if (stopped) {
            // Remove from cache
            await storage.del(`stream:${streamId}`);
            
            res.json({
                success: true,
                message: 'Stream stopped successfully'
            });
        } else {
            res.status(404).json({ error: 'Stream not found' });
        }
        
    } catch (error) {
        console.error('Error stopping stream:', error);
        res.status(500).json({ error: 'Failed to stop stream' });
    }
});

/**
 * Get stream status
 * GET /api/stream/status/:streamId
 */
app.get('/api/stream/status/:streamId', async (req, res) => {
    try {
        const { streamId } = req.params;
        
        const stream = activeStreams.get(streamId);
        if (stream) {
            res.json({
                success: true,
                streamId,
                status: 'active',
                sourceUrl: stream.sourceUrl,
                streamType: stream.streamType,
                hlsUrl: stream.hlsUrl,
                startTime: stream.startTime
            });
        } else {
            // Check cache
            const cachedStream = await storage.get(`stream:${streamId}`);
            if (cachedStream) {
                const streamData = JSON.parse(cachedStream);
                res.json({
                    success: true,
                    streamId,
                    status: 'cached',
                    ...streamData
                });
            } else {
                res.status(404).json({ error: 'Stream not found' });
            }
        }
        
    } catch (error) {
        console.error('Error getting stream status:', error);
        res.status(500).json({ error: 'Failed to get stream status' });
    }
});

/**
 * List all active streams
 * GET /api/streams
 */
app.get('/api/streams', (req, res) => {
    try {
        const streams = Array.from(activeStreams.entries()).map(([id, stream]) => ({
            streamId: id,
            sourceUrl: stream.sourceUrl,
            streamType: stream.streamType,
            hlsUrl: stream.hlsUrl,
            startTime: stream.startTime
        }));
        
        res.json({
            success: true,
            streams,
            count: streams.length
        });
        
    } catch (error) {
        console.error('Error listing streams:', error);
        res.status(500).json({ error: 'Failed to list streams' });
    }
});

/**
 * Health check
 * GET /health
 */
app.get('/health', (req, res) => {
    res.json({
        success: true,
        message: 'Streaming server is running',
        activeStreams: activeStreams.size,
        uptime: process.uptime()
    });
});

// Cleanup on exit
process.on('SIGTERM', () => {
    console.log('Shutting down streaming server...');
    
    // Stop all active streams
    for (const [streamId] of activeStreams) {
        stopStream(streamId);
    }
    
    // Close Redis connection
    if (redisClient) {
        redisClient.quit();
    }
    
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('Shutting down streaming server...');
    
    // Stop all active streams
    for (const [streamId] of activeStreams) {
        stopStream(streamId);
    }
    
    // Close Redis connection
    if (redisClient) {
        redisClient.quit();
    }
    
    process.exit(0);
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🎥 SPARKA Streaming Server running on port ${PORT}`);
    console.log(`📡 HLS streams available at: http://localhost:${PORT}/hls/`);
    console.log(`🔧 API endpoints available at: http://localhost:${PORT}/api/`);
});