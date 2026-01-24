# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Playwright environment variables
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* ./

# Install uv and Python dependencies with BuildKit cache mount
# --no-install-project: Skip installing the project itself (we just need dependencies)
# --frozen: Use lockfile without updating it
RUN --mount=type=cache,target=/root/.cache \
    pip install uv && \
    uv sync --frozen --no-dev --no-install-project

# Install Playwright browsers (Chromium only for headless automation)
# This downloads the browser binaries needed for Playwright
# --no-project: Run in the environment but don't try to install the project
RUN uv run --no-project python -m playwright install chromium

# Copy application code (this layer will be invalidated on code changes)
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command (will be overridden by docker-compose)
CMD ["uv", "run", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
