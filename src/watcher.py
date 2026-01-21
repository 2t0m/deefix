"""
Watchdog event handler for monitoring new MP3 files.
"""

import os
import sys
from watchdog.events import FileSystemEventHandler
from .file_utils import is_in_hidden_folder, is_duplicate_and_remove, wait_for_file_ready


class MP3Handler(FileSystemEventHandler):
    """Watchdog event handler for new MP3 files.
    
    Monitors for new MP3 files, waits for transfer completion,
    optionally removes duplicates, and processes them.
    """
    
    def __init__(self, process_file_func):
        """Initialize handler with processing function.
        
        Args:
            process_file_func: Function to call for processing MP3 files
        """
        super().__init__()
        self.process_file_func = process_file_func

    def on_created(self, event):
        """Handle file creation events.
        
        Args:
            event: Watchdog file system event
        """
        # Only process MP3 files
        if event.is_directory or not event.src_path.lower().endswith('.mp3'):
            return
        
        # Skip hidden folders
        if is_in_hidden_folder(event.src_path):
            print(f"File in hidden folder, ignored: {event.src_path}", file=sys.stderr)
            return
        
        print(f"New file detected: {event.src_path} (waiting for transfer to complete)", file=sys.stderr)
        
        # Wait for file transfer to complete
        if not wait_for_file_ready(event.src_path):
            print(f"Timeout waiting for file transfer: {event.src_path}", file=sys.stderr)
            return
        
        print(f"File ready: {event.src_path}", file=sys.stderr)
        
        # Check and remove duplicates if enabled
        if os.environ.get('REMOVE_DUPLICATES', 'false').lower() == 'true':
            if is_duplicate_and_remove(event.src_path):
                return
        
        # Process the file
        print(f"Processing file: {event.src_path}", file=sys.stderr)
        self.process_file_func(event.src_path)
        print(f"File processing completed: {event.src_path}", file=sys.stderr)
        print("─" * 80, file=sys.stderr)
