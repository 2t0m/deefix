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
    """
    return {
        'fix_tags': os.environ.get('FIX_TAGS', 'true').lower() == 'true',
        'fetch_lyrics': os.environ.get('FETCH_LYRICS', 'false').lower() == 'true',
        'remove_duplicates': os.environ.get('REMOVE_DUPLICATES', 'false').lower() == 'true',
        'fetch_video_artwork': os.environ.get('FETCH_VIDEO_ARTWORK', 'true').lower() == 'true',
        'fix_gain': os.environ.get('FIX_GAIN', 'false').lower() == 'true',
    }
