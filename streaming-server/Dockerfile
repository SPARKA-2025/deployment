FROM node:18-alpine

# Install FFmpeg and curl for health checks
RUN apk add --no-cache ffmpeg curl

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Create directories for HLS streams
RUN mkdir -p /app/streams
RUN mkdir -p /app/public/hls

# Expose port
EXPOSE 8005

# Start the application
CMD ["npm", "start"]