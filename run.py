import sqlite3
import os
import sys
import time
import sqlite3
import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# SQLite utility functions
DB_PATH = os.path.join(os.environ.get('DB_FOLDER', '.'), 'mp3_processed.db')
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS processed_files (filepath TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def is_file_processed(file_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM processed_files WHERE filepath=?', (file_path,))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_file_processed(file_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO processed_files (filepath) VALUES (?)', (file_path,))
    conn.commit()
    conn.close()

def is_in_hidden_folder(file_path):
    """Check if the file path contains any hidden folder (starting with a dot)"""
    parts = os.path.normpath(file_path).split(os.sep)
    return any(part.startswith('.') and part != '.' and part != '..' for part in parts)

def is_duplicate_and_remove(file_path):
    """Check if file has (n) suffix and is duplicate of original, then remove it"""
    import re
    
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    
    # Match pattern like "Song (1)" or "Song (2)"
    match = re.match(r'^(.+?)\s*\(\d+\)$', name)
    if match:
        original_name = match.group(1)
        original_path = os.path.join(dir_name, original_name + ext)
        # Check if original file exists in same folder
        if os.path.exists(original_path):
            try:
                os.remove(file_path)
                print(f"Removed duplicate: {base_name} (original exists: {original_name}{ext})", file=sys.stderr)
                return True
            except Exception as e:
                print(f"Error removing duplicate {file_path}: {e}", file=sys.stderr)
    return False

def wait_for_file_ready(file_path, timeout=30, check_interval=0.5):
    """Wait until file is fully transferred by checking if size stabilizes"""
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

# Handler for new files
class MP3Handler(FileSystemEventHandler):
    def __init__(self, process_file_func):
        super().__init__()
        self.process_file_func = process_file_func

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.mp3'):
            if is_in_hidden_folder(event.src_path):
                print(f"File in hidden folder, ignored: {event.src_path}", file=sys.stderr)
                return
            print(f"New file detected: {event.src_path} (waiting for transfer to complete)", file=sys.stderr)
            if wait_for_file_ready(event.src_path):
                print(f"File ready: {event.src_path}", file=sys.stderr)
                # Check and remove if it's a duplicate (if enabled)
                if os.environ.get('REMOVE_DUPLICATES', 'false').lower() == 'true':
                    if is_duplicate_and_remove(event.src_path):
                        return
                print(f"Processing file: {event.src_path}", file=sys.stderr)
                self.process_file_func(event.src_path)
                print(f"File processing completed: {event.src_path}", file=sys.stderr)
            else:
                print(f"Timeout waiting for file transfer: {event.src_path}", file=sys.stderr)

# Function to process a single mp3 file
def process_mp3_file(file_path, stats=None):
    if is_file_processed(file_path):
        print(f"File already processed, ignored: {file_path}")
        if stats:
            stats['already_processed'] += 1
        return 'already_processed'
    print(f"Reading tags from: {file_path}", file=sys.stderr)
    tags, artist, album, title = get_mp3_tags(file_path)
    print(f"File: {file_path}")
    if artist and title:
        track_ids = search_deezer_track(artist, album, title)
        if track_ids:
            mp3_isrc = tags.get('isrc', [''])[0] if isinstance(tags.get('isrc'), list) else tags.get('isrc', '')
            print(f"MP3 ISRC: '{mp3_isrc}'")
            
            # Try each track ID until we find one with matching ISRC
            for idx, track_id in enumerate(track_ids, 1):
                info = get_deezer_track_info(track_id)
                if not info:
                    continue
                    
                # Get albumartist from album artist, fallback to main artist
                album_artist = info.get('album', {}).get('artist', {}).get('name') if info.get('album', {}).get('artist') else None
                if not album_artist:
                    album_artist = info.get('artist', {}).get('name')
                
                deezer_tags = {
                    'album': info.get('album', {}).get('title'),
                    'title': info.get('title'),
                    'artist': info.get('artist', {}).get('name'),
                    'albumartist': album_artist,
                    'discnumber': str(info.get('disk_number')),
                    'tracknumber': str(info.get('track_position')),
                    'isrc': info.get('isrc'),
                    'genre': info.get('genre'),
                    'date': info.get('release_date'),
                    'gain': str(info.get('gain')) if info.get('gain') is not None else None,
                }
                deezer_isrc = deezer_tags.get('isrc', '')
                
                print(f"Result {idx}/{len(track_ids)} - Deezer ISRC: '{deezer_isrc}'")
                
                if mp3_isrc and deezer_isrc and mp3_isrc == deezer_isrc:
                    print(f"ISRC match found on result {idx}!")
                    for k in ['album','title','albumartist','discnumber','tracknumber','genre','date','gain']:
                        val = deezer_tags.get(k)
                        if val is not None:
                            set_mp3_tag(file_path, k, val)
                    contributors = [c['name'] for c in info.get('contributors', [])]
                    if contributors:
                        set_mp3_tag(file_path, 'artist', ', '.join(contributors))
                    
                    # Search for synced lyrics if enabled
                    if os.environ.get('FETCH_LYRICS', 'false').lower() == 'true':
                        duration = get_audio_duration(file_path)
                        lyrics = search_lrclib_lyrics(
                            deezer_tags.get('artist', artist),
                            deezer_tags.get('title', title),
                            deezer_tags.get('album', album),
                            duration
                        )
                        if lyrics:
                            set_mp3_tag(file_path, 'lyrics', lyrics)
                    
                    print("Tags updated from Deezer (identical ISRC)\n")
                    mark_file_processed(file_path)
                    if stats:
                        stats['isrc_match'] += 1
                    return 'isrc_match'
                    break
            else:
                # No matching ISRC found in any result
                if not mp3_isrc:
                    print("No ISRC in MP3 file, tags not updated\n")
                    if stats:
                        stats['no_isrc_in_mp3'] += 1
                    return 'no_isrc_in_mp3'
                else:
                    print(f"No matching ISRC found in {len(track_ids)} Deezer results, tags not updated\n")
                    if stats:
                        stats['no_matching_isrc'] += 1
                    return 'no_matching_isrc'
        else:
            print("No Deezer results\n")
            if stats:
                stats['no_deezer_results'] += 1
            return 'no_deezer_results'
    else:
        print("Incomplete tags\n")
        if stats:
            stats['incomplete_tags'] += 1
        return 'incomplete_tags'

def set_mp3_tag(file_path, tag, value):
    try:
        try:
            audio = EasyID3(file_path)
        except ID3NoHeaderError:
            audio = EasyID3()
            audio.save(file_path)
            audio = EasyID3(file_path)
        if tag == 'gain':
            # Use the TXXX:replaygain_track_gain tag for gain
            from mutagen.id3 import ID3, TXXX
            id3 = ID3(file_path)
            id3.delall('TXXX:replaygain_track_gain')
            id3.add(TXXX(encoding=3, desc='replaygain_track_gain', text=str(value)))
            id3.save(file_path)
            print(f"Tag 'replaygain_track_gain' updated in {file_path}: {value}")
        elif tag == 'lyrics':
            # Use USLT frame for synced lyrics
            from mutagen.id3 import ID3, USLT
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

def get_mp3_tags(file_path):
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

def get_audio_duration(file_path):
    """Get audio duration in seconds"""
    try:
        from mutagen.mp3 import MP3
        audio = MP3(file_path)
        return int(audio.info.length)
    except Exception as e:
        print(f"Error getting duration: {e}", file=sys.stderr)
        return None

def search_deezer_track(artist, album, title):
    import urllib.parse
    query = f"{artist} {album} {title}"
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.deezer.com/search?q={encoded_query}"
    print(f"Calling Deezer Search URL: {url}")
    response = requests.get(url)
    track_ids = []
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            # Return up to 5 track IDs
            track_ids = [track['id'] for track in data['data'][:5]]
            print(f"Found {len(track_ids)} results with full query")
            return track_ids
    
    # If no results, try simplified query (artist + title only)
    print("No results with full query, trying simplified search...")
    query_simple = f"{artist} {title}"
    encoded_query_simple = urllib.parse.quote(query_simple)
    url_simple = f"https://api.deezer.com/search?q={encoded_query_simple}"
    print(f"Calling Deezer Search URL: {url_simple}")
    response_simple = requests.get(url_simple)
    if response_simple.status_code == 200:
        data_simple = response_simple.json()
        if data_simple['data']:
            # Return up to 5 track IDs
            track_ids = [track['id'] for track in data_simple['data'][:5]]
            print(f"Found {len(track_ids)} results with simplified query")
            return track_ids
    
    return []

def search_lrclib_lyrics(artist, title, album=None, duration=None):
    """Search for synchronized lyrics on lrclib.net"""
    try:
        params = {
            'artist_name': artist,
            'track_name': title,
        }
        if album:
            params['album_name'] = album
        if duration:
            params['duration'] = duration
        
        url = "https://lrclib.net/api/get"
        print(f"Searching lrclib for lyrics: {artist} - {title}", file=sys.stderr)
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            synced_lyrics = data.get('syncedLyrics')
            if synced_lyrics:
                print(f"Found synced lyrics on lrclib")
                return synced_lyrics
        elif response.status_code == 404:
            print(f"No lyrics found on lrclib")
        else:
            print(f"lrclib returned status {response.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"Error searching lrclib: {e}", file=sys.stderr)
    return None

def get_deezer_track_info(track_id):
    url = f"https://api.deezer.com/track/{track_id}"
    print(f"Calling Deezer Track URL: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def main(folder):
    init_db()
    
    # Initialize statistics
    stats = {
        'total_files': 0,
        'isrc_match': 0,
        'no_isrc_in_mp3': 0,
        'no_matching_isrc': 0,
        'no_deezer_results': 0,
        'incomplete_tags': 0,
        'already_processed': 0,
        'hidden_folders': 0,
        'duplicates_removed': 0
    }
    
    print("Starting initial scan...", file=sys.stderr)
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.mp3'):
                path = os.path.join(root, file)
                if is_in_hidden_folder(path):
                    print(f"File in hidden folder, ignored: {path}", file=sys.stderr)
                    stats['hidden_folders'] += 1
                    continue
                # Check and remove if it's a duplicate (if enabled)
                if os.environ.get('REMOVE_DUPLICATES', 'false').lower() == 'true':
                    if is_duplicate_and_remove(path):
                        stats['duplicates_removed'] += 1
                        continue
                stats['total_files'] += 1
                process_mp3_file(path, stats)
    
    # Display statistics
    print("\n" + "="*60, file=sys.stderr)
    print("INITIAL SCAN STATISTICS", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"Total files processed: {stats['total_files']}", file=sys.stderr)
    print(f"  ✓ ISRC match (tags updated): {stats['isrc_match']}", file=sys.stderr)
    print(f"  ✗ No ISRC in MP3 file: {stats['no_isrc_in_mp3']}", file=sys.stderr)
    print(f"  ✗ No matching ISRC in Deezer results: {stats['no_matching_isrc']}", file=sys.stderr)
    print(f"  ✗ No Deezer results: {stats['no_deezer_results']}", file=sys.stderr)
    print(f"  ✗ Incomplete tags (no artist/title): {stats['incomplete_tags']}", file=sys.stderr)
    print(f"  - Already processed (skipped): {stats['already_processed']}", file=sys.stderr)
    if stats['hidden_folders'] > 0:
        print(f"  - Hidden folders (skipped): {stats['hidden_folders']}", file=sys.stderr)
    if stats['duplicates_removed'] > 0:
        print(f"  - Duplicates removed: {stats['duplicates_removed']}", file=sys.stderr)
    
    if stats['total_files'] > 0:
        success_rate = (stats['isrc_match'] / stats['total_files']) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%", file=sys.stderr)
    print("="*60 + "\n", file=sys.stderr)

    # Watcher for new files
    print("Activating watcher for new MP3 files...", file=sys.stderr)
    event_handler = MP3Handler(process_mp3_file)
    observer = Observer()
    observer.schedule(event_handler, folder, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    folder = os.environ.get('MP3_FOLDER_PATH')
    if not folder:
        folder = input("MP3 folder path: ")
    print(f"Monitoring folder: {folder}", file=sys.stderr)
    main(folder)