# Stage 1: Build
FROM node:18-alpine as build
WORKDIR /app

# Copy dependencies and install
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build
COPY . .

# Allow passing VITE env vars at build time so they are available for Vite
ARG VITE_API_URL
ARG VITE_OPENAI_API_KEY
ARG VITE_OPENAI_PROJECT_ID

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_OPENAI_API_KEY=${VITE_OPENAI_API_KEY}
ENV VITE_OPENAI_PROJECT_ID=${VITE_OPENAI_PROJECT_ID}

RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html
# Default nginx.conf will suffice, but we provide a SPA fallback
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
