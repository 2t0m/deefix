"""
DeeFix - MP3 Tag Fixer and Artwork Generator
Automatically processes MP3 files to fix tags using Deezer API and generate artwork from Apple Music.

This file is kept for backward compatibility.
The code has been refactored into separate modules in the src/ directory.
"""

import sys
from src.main import main

if __name__ == "__main__":
    folder = '/music'
    print(f"Monitoring folder: {folder}", file=sys.stderr)
    main(folder)