"""
Artwork generation from Apple Music.
Fetches and generates cover.webp artwork from Apple Music album video.
"""

import os
import re
import sys
import subprocess
import requests
from ddgs import DDGS


def fetch_video_artwork(artist, album, title, file_path, stats=None):
    """Fetch and generate cover.webp artwork from Apple Music album video.
    
    Process:
    1. Search DuckDuckGo for Apple Music album page
    2. Extract m3u8 video URL from the page
    3. Use ffmpeg to generate a 720x720 webp image
    
    Args:
        artist: Artist name
        album: Album name
        title: Track title
        file_path: Path to the MP3 file (artwork saved in same directory)
        stats: Statistics dictionary (optional)
        
    Returns:
        True if artwork was generated or already exists, False otherwise
    """
    out_dir = os.path.dirname(file_path)
    out_path = os.path.join(out_dir, "cover.webp")
    
    # Skip if artwork already exists
    if os.path.exists(out_path):
        print(f"cover.webp already exists at {out_path}, skipping.", file=sys.stderr)
        return True  # Already exists, consider as success
    
    try:
        # Step 1: Search for Apple Music album page
        query = f"{artist} {album} {title} site:music.apple.com"
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, region='wt-wt', safesearch='Off', max_results=10):
                url = r.get('href') or r.get('url')
                if url:
                    results.append(url)
        
        # Filter for album links only
        album_links = [u for u in results if "/album/" in u]
        if not album_links:
            print("No Apple Music album URL found in search results.", file=sys.stderr)
            print(f"Search results: {results}", file=sys.stderr)
            return False
        
        apple_url = album_links[0]
        
        # Step 2: Fetch Apple Music page
        headers = {"User-Agent": "Mozilla/5.0"}
        page = requests.get(apple_url, headers=headers, timeout=10)
        if page.status_code != 200:
            print(f"Apple Music error: {page.status_code}", file=sys.stderr)
            return False
        
        # Step 3: Extract m3u8 video URL
        m3u8_url = None
        for match in re.finditer(r'<amp-ambient-video[^>]*src=\"([^\"]+\.m3u8)\"', page.text):
            candidate = match.group(1)
            if candidate.startswith("https://"):
                m3u8_url = candidate
                break
        
        if not m3u8_url:
            print("No m3u8 found on the album page from Apple Music.", file=sys.stderr)
            return False
        
        # Step 4: Generate cover.webp with ffmpeg
        ffmpeg_cmd = [
            "ffmpeg",
            "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "-i", m3u8_url,
            "-vf", "scale=720:720:flags=lanczos",
            "-loop", "0",
            out_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Artwork generated successfully: {out_path}", file=sys.stderr)
        if stats is not None:
            stats['artwork_fetched'] += 1
        return True  # Success
            
    except Exception as e:
        print(f"Error fetch_video_artwork: {e}", file=sys.stderr)
        return False
