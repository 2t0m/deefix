# DeeFix

> Automatically update MP3 tags using the Deezer API and other sources.

## Quick Start

### Run with Docker

```bash
docker-compose up -d
```

Main environment variables (set in your environment or docker-compose):
- `FIX_TAGS`: Fix tags using Deezer (ISRC)
- `FETCH_LYRICS`: Fetch synchronized lyrics
- `REMOVE_DUPLICATES`: Remove duplicate files
- `FETCH_VIDEO_ARTWORK`: Generate 720x720 artwork from Apple Music
- `FIX_GAIN`: Normalize audio volume
- `ANALYZE_ESSENTIA`: Audio analysis with Essentia (mood tags)
- `ORGANIZE_MP3`: Organize MP3 files by artist/album

## Features
- Fix MP3 tags via Deezer (ISRC)
- High-quality artwork from Apple Music
- Synchronized lyrics
- Volume normalization (ReplayGain)
- Optional audio analysis (Essentia)
- Automatic library organization
- Automatic duplicate removal
- Real-time folder monitoring
- Ignores hidden folders
- SQLite database to avoid duplicate processing