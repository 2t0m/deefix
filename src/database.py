"""
Database operations for tracking processed MP3 files.
Uses SQLite to store processing status.
"""

import sqlite3
from .config import DB_PATH


def init_db():
    """Initialize the SQLite database for tracking processed files.
    
    Creates a table with columns for tracking which processing steps
    have been completed for each file.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS processed_files (
        filepath TEXT PRIMARY KEY,
        tags_fixed INTEGER DEFAULT 0,
        lyrics_fetched INTEGER DEFAULT 0,
        artwork_generated INTEGER DEFAULT 0,
        gain_applied INTEGER DEFAULT 0,
        last_processed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


def is_file_processed(file_path):
    """Check if a file has already been processed and get processing details.
    
    Args:
        file_path: Path to the MP3 file
        
    Returns:
        Dictionary with processing status (tags_fixed, lyrics_fetched,
        artwork_generated, gain_applied) or None if not processed
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT tags_fixed, lyrics_fetched, artwork_generated, gain_applied 
                 FROM processed_files WHERE filepath=?''', (file_path,))
    result = c.fetchone()
    conn.close()
    if result:
        return {
            'tags_fixed': bool(result[0]),
            'lyrics_fetched': bool(result[1]),
            'artwork_generated': bool(result[2]),
            'gain_applied': bool(result[3])
        }
    return None


def update_file_processing_status(file_path, tags_fixed=False, lyrics_fetched=False, 
                                   artwork_generated=False, gain_applied=False):
    """Update the processing status for a file in the database.
    
    Args:
        file_path: Path to the MP3 file
        tags_fixed: Whether tags were fixed
        lyrics_fetched: Whether lyrics were fetched
        artwork_generated: Whether artwork was generated
        gain_applied: Whether gain normalization was applied
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO processed_files 
                 (filepath, tags_fixed, lyrics_fetched, artwork_generated, gain_applied)
                 VALUES (?, ?, ?, ?, ?)
                 ON CONFLICT(filepath) DO UPDATE SET
                 tags_fixed = excluded.tags_fixed,
                 lyrics_fetched = excluded.lyrics_fetched,
                 artwork_generated = excluded.artwork_generated,
                 gain_applied = excluded.gain_applied,
                 last_processed = CURRENT_TIMESTAMP''',
              (file_path, int(tags_fixed), int(lyrics_fetched), 
               int(artwork_generated), int(gain_applied)))
    conn.commit()
    conn.close()
