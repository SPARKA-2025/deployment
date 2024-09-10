FROM node:18-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install

COPY . .

# Build the app with environment variables
ENV REACT_APP_API_URL="35.219.75.160"

EXPOSE 5173

RUN npm run build

CMD ["npm", "run", "dev"]