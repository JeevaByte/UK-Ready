# =============================================================================
# UKReady Frontend — Dockerfile
# =============================================================================
# Uses Node.js 20 LTS. In development (Docker Compose), the container
# runs `npm run dev` with source mounted as a volume for hot reload.
# =============================================================================

FROM node:20-alpine AS base

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source
COPY . .

EXPOSE 3000

# Development: hot reload via volume mount in docker-compose.yml
CMD ["npm", "run", "dev"]
