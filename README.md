# DeeFix

> Automatically update MP3 tags using the Deezer API and more.

## Quick Usage

### Docker

```bash
docker-compose up -d

Main environment variables:
- `FIX_TAGS=true`: enable Deezer tag fixing (ISRC matching)
- `FETCH_LYRICS=true`: fetch synchronized lyrics from lrclib.net
- `REMOVE_DUPLICATES=true`: remove duplicate files (e.g., "Song (1).mp3")
- `FETCH_VIDEO_ARTWORK=true`: generate 720x720 WebP artwork from Apple Music
- `FIX_GAIN=true`: normalize audio gain using loudgain (ReplayGain tags, --tagmode=i)
- `ANALYZE_ESSENTIA=false`: analyze tracks with Essentia and write ID3 tags (including mood)
- `ORGANIZE_MP3=true`: move each processed MP3 to `/music/Artist/Album/Title.mp3` (with duplicate handling)

When `ORGANIZE_MP3=true`, after all processing, each MP3 is moved to a structured folder tree:

```
/music/Artist/Album/Title.mp3
```

If a file with the same name exists:
- If `REMOVE_DUPLICATES=true`, the new file is deleted and the existing one is kept.
- If `REMOVE_DUPLICATES=false`, the new file is renamed as `Title (1).mp3`, `Title (2).mp3`, etc.

After each move or deletion, any empty folders left behind are automatically removed to keep your library clean.



Main environment variables:
- `FIX_TAGS=true`: enable Deezer tag fixing (ISRC matching)
- `FETCH_LYRICS=true`: fetch synchronized lyrics from lrclib.net
- `REMOVE_DUPLICATES=true`: remove duplicate files (e.g., "Song (1).mp3")
- `FETCH_VIDEO_ARTWORK=true`: generate 720x720 WebP artwork from Apple Music
- `FIX_GAIN=true`: normalize audio gain using loudgain (ReplayGain tags, --tagmode=i)
- `ANALYZE_ESSENTIA=false`: analyze tracks with Essentia and write ID3 tags (including mood)
-


## Features
- Scan and update MP3 tags from Deezer (ISRC matching)
- Generate high-quality artwork from Apple Music videos (720x720 WebP)
- Fetch synchronized lyrics from lrclib.net
- Audio gain normalization using loudgain (ReplayGain tags)
- Optional audio analysis using Essentia with direct ID3 tagging (including mood)
- Automatic duplicate file removal
- Real-time folder monitoring
- Ignores hidden folders
- SQLite database to avoid duplicate processing
