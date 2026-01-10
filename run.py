import sqlite3
# Organized imports
import os
import sys
import time
import sqlite3
import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError
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
                self.process_file_func(event.src_path)
            else:
                print(f"Timeout waiting for file transfer: {event.src_path}", file=sys.stderr)

# Function to process a single mp3 file
def process_mp3_file(file_path):
    if is_file_processed(file_path):
        print(f"File already processed, ignored: {file_path}")
        return
    tags, artist, album, title = get_mp3_tags(file_path)
    print(f"File: {os.path.basename(file_path)}")
    if artist and title:
        track_id = search_deezer_track(artist, album, title)
        if track_id:
            info = get_deezer_track_info(track_id)
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
            mp3_isrc = tags.get('isrc', [''])[0] if isinstance(tags.get('isrc'), list) else tags.get('isrc', '')
            deezer_isrc = deezer_tags.get('isrc', '')
            if mp3_isrc and deezer_isrc and mp3_isrc == deezer_isrc:
                for k in ['album','title','albumartist','discnumber','tracknumber','genre','date','gain']:
                    val = deezer_tags.get(k)
                    if val is not None:
                        set_mp3_tag(file_path, k, val)
                contributors = [c['name'] for c in info.get('contributors', [])]
                if contributors:
                    set_mp3_tag(file_path, 'artist', ', '.join(contributors))
                print("Tags updated from Deezer (identical ISRC)\n")
                mark_file_processed(file_path)
        else:
            print("No Deezer results\n")
    else:
        print("Incomplete tags\n")

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

def search_deezer_track(artist, album, title):
    import urllib.parse
    query = f"{artist} {album} {title}"
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.deezer.com/search?q={encoded_query}"
    print(f"Calling Deezer Search URL: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            track = data['data'][0]
            return track['id']
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
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.mp3'):
                path = os.path.join(root, file)
                if is_in_hidden_folder(path):
                    print(f"File in hidden folder, ignored: {path}", file=sys.stderr)
                    continue
                process_mp3_file(path)

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