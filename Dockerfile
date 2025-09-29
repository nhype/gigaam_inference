# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create directories for certificates
RUN mkdir -p /app/certs

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# Add appuser to docker group to access Docker socket for health checks
RUN groupadd -g 988 docker 2>/dev/null || true && usermod -aG docker appuser
USER appuser

# Expose port 4443 (HTTPS only)
EXPOSE 4443

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -k -f https://localhost:4443/health || exit 1

# Run the application
CMD ["python", "main.py"] 