"""
Deezer API operations.
Handles searching for tracks and fetching track information from Deezer.
"""

import requests
from urllib.parse import quote


def search_deezer_track(artist, album, title):
    """Search Deezer for tracks matching artist, album, and title.
    
    First tries a full query with all three parameters. If no results,
    falls back to artist + title only.
    
    Args:
        artist: Artist name
        album: Album name
        title: Track title
        
    Returns:
        List of up to 5 track IDs, or empty list if no results
    """
    # Try full query first
    query = f"{artist} {album} {title}"
    url = f"https://api.deezer.com/search?q={quote(query)}"
    print(f"Calling Deezer Search URL: {url}")
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            track_ids = [track['id'] for track in data['data'][:5]]
            print(f"Found {len(track_ids)} results with full query")
            return track_ids
    
    # Fallback to simplified query (artist + title only)
    print("No results with full query, trying simplified search...")
    query_simple = f"{artist} {title}"
    url_simple = f"https://api.deezer.com/search?q={quote(query_simple)}"
    print(f"Calling Deezer Search URL: {url_simple}")
    
    response_simple = requests.get(url_simple)
    if response_simple.status_code == 200:
        data_simple = response_simple.json()
        if data_simple.get('data'):
            track_ids = [track['id'] for track in data_simple['data'][:5]]
            print(f"Found {len(track_ids)} results with simplified query")
            return track_ids
    
    return []


def get_deezer_track_info(track_id):
    """Fetch detailed track info from Deezer API.
    
    Args:
        track_id: Deezer track ID
        
    Returns:
        Dictionary of track info, or None on error
    """
    url = f"https://api.deezer.com/track/{track_id}"
    print(f"Calling Deezer Track URL: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None
