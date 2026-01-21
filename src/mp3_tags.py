"""
MP3 tag operations using mutagen.
Handles reading and writing ID3 tags.
"""

import sys
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError, ID3, TXXX, USLT
from mutagen.mp3 import MP3


def get_mp3_tags(file_path):
    """Read tags from an MP3 file.
    
    Args:
        file_path: Path to the MP3 file
        
    Returns:
        Tuple of (tags dict, artist, album, title)
    """
    try:
        audio = EasyID3(file_path)
        tags = dict(audio)
        artist = tags.get('artist', [''])[0]
        album = tags.get('album', [''])[0]
        title = tags.get('title', [''])[0]
        return tags, artist, album, title
    except Exception as e:
        print(f"Error reading tags: {e}", file=sys.stderr)
        return {}, '', '', ''


def check_tags(tags):
    """Extract and validate basic tags from MP3 metadata.
    
    Args:
        tags: Dictionary of MP3 tags
        
    Returns:
        Tuple of (artist, album, title, has_complete_tags)
    """
    artist = tags.get('artist', [''])[0]
    title = tags.get('title', [''])[0]
    album = tags.get('album', [''])[0]
    return artist, album, title, bool(artist and title)


def set_mp3_tag(file_path, tag, value):
    """Set a tag in an MP3 file using mutagen.
    
    Handles special cases for gain (replaygain) and lyrics (USLT frame).
    
    Args:
        file_path: Path to the MP3 file
        tag: Tag name to set
        value: Value to set for the tag
    """
    try:
        try:
            audio = EasyID3(file_path)
        except ID3NoHeaderError:
            audio = EasyID3()
            audio.save(file_path)
            audio = EasyID3(file_path)
        
        if tag == 'gain':
            # Use TXXX:replaygain_track_gain frame
            id3 = ID3(file_path)
            id3.delall('TXXX:replaygain_track_gain')
            id3.add(TXXX(encoding=3, desc='replaygain_track_gain', text=str(value)))
            id3.save(file_path)
            print(f"Tag 'replaygain_track_gain' updated in {file_path}: {value}")
        elif tag == 'lyrics':
            # Use USLT frame for synced lyrics
            id3 = ID3(file_path)
            id3.delall('USLT')
            id3.add(USLT(encoding=3, lang='eng', desc='', text=value))
            id3.save(file_path)
            print(f"Synced lyrics added to {file_path}")
        else:
            audio[tag] = value if isinstance(value, list) else [value]
            audio.save()
            print(f"Tag '{tag}' updated in {file_path}: {value}")
    except Exception as e:
        print(f"Error in set_mp3_tag on {file_path}: {e}", file=sys.stderr)


def get_audio_duration(file_path):
    """Get audio duration in seconds.
    
    Args:
        file_path: Path to the MP3 file
        
    Returns:
        Duration in seconds as int, or None on error
    """
    try:
        audio = MP3(file_path)
        return int(audio.info.length)
    except Exception as e:
        print(f"Error getting duration: {e}", file=sys.stderr)
        return None
