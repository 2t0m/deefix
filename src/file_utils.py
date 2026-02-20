def move_mp3_to_library(file_path, artist, album, title, music_root="/music"):
    """Move MP3 file to ArtistAlbum/Album/Title.mp3, handle duplicates."""
    import shutil
    import unicodedata
    import re
    import os
    import sys
    
    def safe_name(name):
        # Remove forbidden chars and normalize
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        name = name.strip().replace('  ', ' ')
        return name or 'Unknown'
    
    artist_dir = safe_name(artist)
    album_dir = safe_name(album)
    title_file = safe_name(title) + ".mp3"
    albumartist_dir = safe_name(artist)  # 'artist' is actually albumartist in processor.py
    dest_dir = os.path.join(music_root, albumartist_dir, album_dir)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, title_file)
    from .config import get_processing_options
    options = get_processing_options()
    remove_duplicates = options.get('remove_duplicates', False)
    removed = False
    if os.path.abspath(file_path) == os.path.abspath(dest_path):
        # File is already in the correct location, no need to move
        return dest_path
    if os.path.exists(dest_path):
        if remove_duplicates:
            # Never delete the source file, just ignore the move
            # (do nothing, do not print any message)
            removed = True
            return dest_path
        else:
            # Rename with (1), (2), ...
            base, ext = os.path.splitext(dest_path)
            i = 1
            new_dest = f"{base} ({i}){ext}"
            while os.path.exists(new_dest):
                i += 1
                new_dest = f"{base} ({i}){ext}"
            dest_path = new_dest
    if not removed:
        shutil.move(file_path, dest_path)
        print(f"Moved MP3 to: {dest_path}", file=sys.stderr)
        # Déplacer cover.webp s'il existe dans le dossier source
        src_cover = os.path.join(os.path.dirname(file_path), 'cover.webp')
        if os.path.exists(src_cover):
            dest_cover = os.path.join(dest_dir, 'cover.webp')
            try:
                shutil.move(src_cover, dest_cover)
                print(f"Moved cover.webp to: {dest_cover}", file=sys.stderr)
            except Exception as e:
                print(f"Error moving cover.webp: {e}", file=sys.stderr)
    # Clean up empty folders up the tree from the original file location
    def cleanup_empty_dirs(path, stop_at=music_root):
        path = os.path.dirname(path)
        stop_at = os.path.abspath(stop_at)
        while os.path.abspath(path).startswith(stop_at) and path != stop_at:
            try:
                if not os.listdir(path):
                    os.rmdir(path)
                    print(f"Removed empty folder: {path}", file=sys.stderr)
                path = os.path.dirname(path)
            except Exception:
                break
    cleanup_empty_dirs(file_path)
    return dest_path
"""
File utilities for DeeFix.
Handles file operations like checking for duplicates, hidden folders, and file readiness.
"""

import os
import re
import sys
import time


def is_in_hidden_folder(file_path):
    """Check if the file path contains any hidden folder (starting with a dot).
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file is in a hidden folder, False otherwise
    """
    parts = os.path.normpath(file_path).split(os.sep)
    return any(part.startswith('.') and part not in ('.', '..') for part in parts)


def is_duplicate_and_remove(file_path):
    """Check if file is a duplicate and remove it.
    
    Detects two types of duplicates:
    1. Files with (n) suffix like 'Song (1).mp3' when 'Song.mp3' exists
    2. Files with different track numbers but same title:
       '05 - Quel jeu elle joue.mp3', 'Quel jeu elle joue.mp3', '03 - Quel jeu elle joue.mp3'
    
    Args:
        file_path: Path to the potentially duplicate file
        
    Returns:
        True if file was a duplicate and was removed, False otherwise
    """
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    
    # Type 1: Check for (n) suffix pattern like "Song (1)" or "Song (2)"
    match = re.match(r'^(.+?)\s*\(\d+\)$', name)
    if match:
        original_name = match.group(1)
        original_path = os.path.join(dir_name, original_name + ext)
        
        if os.path.exists(original_path):
            try:
                os.remove(file_path)
                print(f"Removed duplicate: {base_name} (original exists: {original_name}{ext})", file=sys.stderr)
                return True
            except Exception as e:
                print(f"Error removing duplicate {file_path}: {e}", file=sys.stderr)
                return False
    
    # Type 2: Check for files with same title but different track numbers
    # Normalize the filename by removing track number prefix
    normalized_name = name
    track_patterns = [
        r'^\d{1,3}\s*-\s*',  # "01 - ", "1 - "
        r'^\d{1,3}\.\s*',     # "01. ", "1. "
        r'^\d{1,3}\s+'        # "01 ", "1 "
    ]
    
    for pattern in track_patterns:
        normalized_name = re.sub(pattern, '', normalized_name, count=1)
    
    normalized_name = normalized_name.strip()
    
    # If the filename had a track number prefix, check for duplicates
    if normalized_name != name:
        # Look for other files in the same directory with the same normalized name
        try:
            for other_file in os.listdir(dir_name):
                if not other_file.lower().endswith('.mp3'):
                    continue
                if other_file == base_name:
                    continue
                
                other_name, _ = os.path.splitext(other_file)
                other_normalized = other_name
                
                for pattern in track_patterns:
                    other_normalized = re.sub(pattern, '', other_normalized, count=1)
                other_normalized = other_normalized.strip()
                
                # Found a duplicate with same normalized name
                if other_normalized == normalized_name:
                    other_path = os.path.join(dir_name, other_file)
                    
                    # Keep the file with track number, remove the one without (or keep the first one found)
                    # Priority: keep files with track numbers over files without
                    has_track = name != normalized_name
                    other_has_track = other_name != other_normalized
                    
                    if not has_track and other_has_track:
                        # Current file has no track number, other has track number -> remove current
                        try:
                            os.remove(file_path)
                            print(f"Removed duplicate: {base_name} (keeping: {other_file})", file=sys.stderr)
                            return True
                        except Exception as e:
                            print(f"Error removing duplicate {file_path}: {e}", file=sys.stderr)
                            return False
                    elif has_track and not other_has_track:
                        # Current file has track number, other doesn't -> remove other
                        try:
                            os.remove(other_path)
                            print(f"Removed duplicate: {other_file} (keeping: {base_name})", file=sys.stderr)
                            # Don't return True because we didn't remove the current file
                        except Exception as e:
                            print(f"Error removing duplicate {other_path}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error checking for duplicates in {dir_name}: {e}", file=sys.stderr)
    
    return False


def wait_for_file_ready(file_path, timeout=30, check_interval=0.5):
    """Wait until a file is fully transferred by checking if its size stabilizes.
    
    Args:
        file_path: Path to the file to monitor
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
        
    Returns:
        True if file is ready, False if timeout is reached
    """
    if not os.path.exists(file_path):
        return False
    
    elapsed = 0
    last_size = -1
    stable_count = 0
    
    while elapsed < timeout:
        try:
            current_size = os.path.getsize(file_path)
            if current_size == last_size and current_size > 0:
                stable_count += 1
                if stable_count >= 3:  # Size stable for 3 checks
                    return True
            else:
                stable_count = 0
            last_size = current_size
            time.sleep(check_interval)
            elapsed += check_interval
        except (OSError, IOError):
            time.sleep(check_interval)
            elapsed += check_interval
    
    return False
