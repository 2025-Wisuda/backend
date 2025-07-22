# Use Python 3.12 slim image (latest available)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-mysql-client \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
        gcc \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN adduser --disabled-password --gecos '' appuser

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs && chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port
EXPOSE 8899

# Make setup script executable
RUN chmod +x /app/docker_setup.py

# Run setup and start server
CMD ["python", "/app/docker_setup.py"]
