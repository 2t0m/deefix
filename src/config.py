"""
Configuration module for DeeFix.
Handles environment variables and processing options.
"""

import os

# Database path
DB_PATH = os.path.join('/data', 'mp3_processed.db')


def get_processing_options():
    """Return a dict of all relevant processing options from environment variables.
    
    Returns:
        Dictionary with processing options:
        - fix_tags: Whether to fix MP3 tags using Deezer API
        - fetch_lyrics: Whether to fetch synchronized lyrics
        - remove_duplicates: Whether to remove duplicate files
        - fetch_video_artwork: Whether to generate artwork from Apple Music
        - fix_gain: Whether to apply loudgain normalization
        - analyze_essentia: Whether to analyze tracks with Essentia extractor
        - fix_mp3_permission: Whether to set owner to 1000:1000 on organized files/folders
    """
    return {
        'fix_tags': os.environ.get('FIX_TAGS', 'true').lower() == 'true',
        'fetch_lyrics': os.environ.get('FETCH_LYRICS', 'false').lower() == 'true',
        'remove_duplicates': os.environ.get('REMOVE_DUPLICATES', 'false').lower() == 'true',
        'fetch_video_artwork': os.environ.get('FETCH_VIDEO_ARTWORK', 'true').lower() == 'true',
        'fix_gain': os.environ.get('FIX_GAIN', 'false').lower() == 'true',
        'analyze_essentia': os.environ.get('ANALYZE_ESSENTIA', 'false').lower() == 'true',
        'organize_mp3': os.environ.get('ORGANIZE_MP3', 'false').lower() == 'true',
        'fix_mp3_permission': os.environ.get('FIX_MP3_PERMISSION', 'false').lower() == 'true',
        'call_audiomuse': os.environ.get('AUDIOMUSE_AI_CALL', 'false').lower() == 'true',
        'audiomuse_url': os.environ.get('AUDIOMUSE_AI_URL', '').rstrip('/'),
        'audiomuse_debounce': int(os.environ.get('AUDIOMUSE_AI_DEBOUNCE', '30')),
    }
