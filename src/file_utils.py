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
    """Check if file has (n) suffix and is duplicate of original, then remove it.
    
    Detects files with patterns like 'Song (1).mp3' and removes them if
    the original 'Song.mp3' exists in the same folder.
    
    Args:
        file_path: Path to the potentially duplicate file
        
    Returns:
        True if file was a duplicate and was removed, False otherwise
    """
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    
    # Match pattern like "Song (1)" or "Song (2)"
    match = re.match(r'^(.+?)\s*\(\d+\)$', name)
    if not match:
        return False
        
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
