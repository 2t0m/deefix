FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    loudgain \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (essentia-tensorflow, mutagen, numpy, etc.)
RUN pip install --no-cache-dir essentia-tensorflow mutagen numpy

# Download Essentia TensorFlow models
RUN mkdir -p /root/essentia_models && cd /root/essentia_models && \
    echo "📦 Downloading embedding model..." && \
    wget -q --show-progress https://essentia.upf.edu/models/music-style-classification/discogs-effnet/discogs-effnet-bs64-1.pb && \
    echo "📦 Downloading genre classifier (Discogs 400)..." && \
    wget -q --show-progress https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.pb && \
    wget -q --show-progress https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.json && \
    echo "📦 Downloading mood classifier..." && \
    wget -q --show-progress https://essentia.upf.edu/models/classification-heads/mtg_jamendo_moodtheme/mtg_jamendo_moodtheme-discogs-effnet-1.pb && \
    wget -q --show-progress https://essentia.upf.edu/models/classification-heads/mtg_jamendo_moodtheme/mtg_jamendo_moodtheme-discogs-effnet-1.json

# Copy application code
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Entrypoint
CMD ["python", "run.py"]
