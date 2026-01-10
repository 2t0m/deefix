# DeeFix - MP3 Tag Updater with Deezer

Automatically updates MP3 tags using Deezer API data.

## Features

- Scans MP3 files and updates tags from Deezer
- Monitors folder for new MP3 files
- Skips hidden folders (starting with a dot)
- Persistent SQLite database to avoid reprocessing files

## Docker Deployment

### Using Pre-built Image

Pull and run the latest image from GitHub Container Registry:

```bash
docker run -d \
  --name deefix \
  -e MP3_FOLDER_PATH=/music \
  -e DB_FOLDER=/data \
  -v /path/to/your/music:/music \
  -v ./data:/data \
  --restart unless-stopped \
  ghcr.io/OWNER/deefix:latest
```

Replace `OWNER` with the GitHub username/organization.

### Building from Source

### Prerequisites

- Docker
- Docker Compose

### Quick Start

1. Edit `docker-compose.yml` and change the volume path:
   ```yaml
   volumes:
     - /path/to/your/music:/music  # Change this to your MP3 folder
   ```

2. Build and run:
   ```bash
   docker-compose up -d
   ```

3. View logs:
   ```bash
   docker-compose logs -f
   ```

4. Stop the container:
   ```bash
   docker-compose down
   ```

### Configuration

The MP3 folder path is configured via the `MP3_FOLDER_PATH` environment variable in `docker-compose.yml`.

The database is persisted in the `./data` directory.

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the script:
   ```bash
   python run.py
   ```

   You'll be prompted to enter the MP3 folder path (or set the `MP3_FOLDER_PATH` environment variable).
