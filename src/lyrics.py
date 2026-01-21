"""
Lyrics operations using lrclib.net API.
Fetches synchronized lyrics for tracks.
"""

import sys
import requests


def search_lrclib_lyrics(artist, title, album=None, duration=None):
    """Search for synchronized lyrics on lrclib.net.
    
    Args:
        artist: Artist name
        title: Track title
        album: Album name (optional)
        duration: Track duration in seconds (optional)
        
    Returns:
        Synchronized lyrics string, or None if not found
    """
    try:
        params = {
            'artist_name': artist,
            'track_name': title,
        }
        if album:
            params['album_name'] = album
        if duration:
            params['duration'] = duration
        
        url = "https://lrclib.net/api/get"
        print(f"Searching lrclib for lyrics: {artist} - {title}", file=sys.stderr)
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            synced_lyrics = data.get('syncedLyrics')
            if synced_lyrics:
                print(f"Found synced lyrics on lrclib")
                return synced_lyrics
        elif response.status_code == 404:
            print(f"No lyrics found on lrclib")
        else:
            print(f"lrclib returned status {response.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"Error searching lrclib: {e}", file=sys.stderr)
    return None
