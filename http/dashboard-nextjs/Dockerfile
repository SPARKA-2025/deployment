# Use an official Node.js image as the base image
FROM node:18-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock) into the container
COPY . .

# Install dependencies
RUN npm install

# Build the Next.js app for production
# RUN npm run build

# Expose the port that Next.js listens to
EXPOSE 3000

# Start the Next.js app
CMD ["npm", "run", "dev"]
