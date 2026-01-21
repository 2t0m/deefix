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
- `FIX_TAGS=true`: enable tags fixing
- `FETCH_LYRICS=true`: enable synced lyrics search from lrclib.net
- `REMOVE_DUPLICATES=true`: remove duplicate files
- `FETCH_VIDEO_ARTWORK=true`: enable or disable video artwork retrieval
- `FIX_GAIN=true`: normalize audio gain using loudgain (--tagmode=i)


## Features
- Scan and update MP3 tags from Deezer
- Automatic folder monitoring
- Ignores hidden folders
- SQLite database to avoid duplicate processing
- Lyrics (if enabled) are fetched from lrclib.net
