# Stage 1: Build
FROM node:18-alpine as build
WORKDIR /app

# Copy dependencies and install
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build
COPY . .

# Allow passing VITE env var at build time so it is available for Vite
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html
# Default nginx.conf will suffice, but we provide a SPA fallback
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
