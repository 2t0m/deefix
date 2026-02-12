"""
MP3 tag operations using mutagen.
Handles reading and writing ID3 tags.
"""

import sys
import re
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError, ID3, TXXX, USLT
from mutagen.mp3 import MP3


def extract_isrc_from_comment(comment):
    """Extract ISRC from comment field if present.
    
    Looks for patterns like "ISRC: XXXXX" or "ISRC:XXXXX" in comments.
    
    Args:
        comment: Comment string from MP3 tags
        
    Returns:
        ISRC string if found, None otherwise
    """
    if not comment:
        return None
    
    # Pattern for ISRC: letters and numbers, typically 12 chars
    # More flexible pattern to catch various formats
    match = re.search(r'ISRC[:\s]*([A-Z]{2}[A-Z0-9]{3}\d{7})', comment, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    # Alternative pattern without ISRC prefix but 12 chars format
    match = re.search(r'\b([A-Z]{2}[A-Z0-9]{3}\d{7})\b', comment, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    return None


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
        
        # If no ISRC in standard field, try to extract from comment and save it
        isrc = tags.get('isrc', [''])[0] if isinstance(tags.get('isrc'), list) else tags.get('isrc', '')
        if not isrc:
            # Try EasyID3 comment field
            comment = tags.get('comment', [''])[0] if isinstance(tags.get('comment'), list) else tags.get('comment', '')
            
            # Also check ID3 COMM frames directly for comments
            if not comment:
                try:
                    id3 = ID3(file_path)
                    for frame in id3.getall('COMM'):
                        if frame.text and frame.text[0]:
                            comment = frame.text[0]
                            break
                except:
                    pass
            
            if comment:
                print(f"No ISRC tag, checking comment field: '{comment}'", file=sys.stderr)
            extracted_isrc = extract_isrc_from_comment(comment)
            if extracted_isrc:
                print(f"ISRC extracted from comment: {extracted_isrc} - Writing to ISRC tag and removing all comments", file=sys.stderr)
                
                # Use ID3 directly to remove all comment frames and write ISRC
                try:
                    id3 = ID3(file_path)
                    # Remove all comment frames (ID3v2)
                    id3.delall('COMM')
                    # Save and remove ID3v1 tag entirely (v1=2 removes ID3v1)
                    id3.save(v1=2)
                except:
                    pass
                
                # Write ISRC using EasyID3 and remove comment field
                audio['isrc'] = extracted_isrc
                # Remove comment from EasyID3 if present
                if 'comment' in audio:
                    del audio['comment']
                audio.save()
                
                tags['isrc'] = [extracted_isrc]
            elif comment:
                print(f"Comment exists but no ISRC pattern found", file=sys.stderr)
        
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
