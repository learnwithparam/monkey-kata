# syntax=docker/dockerfile:1.4
FROM node:18-slim

# Install tini for proper signal handling (with BuildKit cache)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Use tini as entrypoint for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Install dependencies first for better caching
COPY package*.json ./

# Install npm dependencies with BuildKit cache mount
# This caches npm package downloads between builds, significantly speeding up rebuilds
# The node_modules will be installed fresh but packages will be fetched from cache
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit

# Copy source code (this layer will be invalidated on code changes)
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (res) => process.exit(res.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

# Command (will be overridden by docker-compose)
# Using exec form for proper signal propagation
CMD ["npm", "run", "dev"]
