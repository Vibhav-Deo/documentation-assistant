FROM python:3.11-slim

# Create non-root user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    linux-libc-dev \
    libc6-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app && \
    chown -R appuser:appuser /home/appuser

USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4000", "--workers", "1"]
