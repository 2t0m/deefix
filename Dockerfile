FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    loudgain \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (essentia-tensorflow, mutagen, numpy, etc.)
RUN pip install --no-cache-dir essentia-tensorflow mutagen numpy

# Copy Essentia TensorFlow models from local models/ directory
RUN mkdir -p /root/essentia_models
COPY models/ /root/essentia_models/

# Copy application code
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Entrypoint
CMD ["python", "run.py"]
