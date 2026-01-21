# DeeFix

> Automatically update MP3 tags using the Deezer API and more.

## Quick Usage

### Docker

```bash
docker-compose up -d
```

Edit the music folder and data path in `docker-compose.yml`:

```yaml
volumes:
  - /path/to/your/mp3:/music
  - ./data:/data
```



Main environment variables:
- `FIX_TAGS=true`: enable Deezer tag fixing (ISRC matching)
- `FETCH_LYRICS=true`: fetch synchronized lyrics from lrclib.net
- `REMOVE_DUPLICATES=true`: remove duplicate files (e.g., "Song (1).mp3")
- `FETCH_VIDEO_ARTWORK=true`: generate 720x720 WebP artwork from Apple Music
- `FIX_GAIN=true`: normalize audio gain using loudgain (ReplayGain tags, --tagmode=i)


## Features
- Scan and update MP3 tags from Deezer (ISRC matching)
- Generate high-quality artwork from Apple Music videos (720x720 WebP)
- Fetch synchronized lyrics from lrclib.net
- Audio gain normalization using loudgain (ReplayGain tags)
- Automatic duplicate file removal
- Real-time folder monitoring
- Ignores hidden folders
- SQLite database to avoid duplicate processing
