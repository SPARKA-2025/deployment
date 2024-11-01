# Base image
FROM node:18-alpine AS base

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build

ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_BASE_URL="http://localhost:5001"

EXPOSE 3000

CMD ["npm", "run", "start"]