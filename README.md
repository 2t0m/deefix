# DeeFix

> Automatically update MP3 tags using the Deezer API.

## Quick Usage

### Docker

```bash
docker-compose up -d
```

Edit the music folder path in `docker-compose.yml`:

```yaml
volumes:
  - /path/to/your/mp3:/music
```


Main environment variables:
- `MP3_FOLDER_PATH`: folder to watch
- `DB_FOLDER`: folder for the SQLite database
- `FETCH_LYRICS=true`: enable synced lyrics search from lrclib.net (optional)
- `REMOVE_DUPLICATES=true`: remove duplicate files (optional)


## Features
- Scan and update MP3 tags from Deezer
- Automatic folder monitoring
- Ignores hidden folders
- SQLite database to avoid duplicate processing
- Lyrics (if enabled) are fetched from lrclib.net
