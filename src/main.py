"""
Main entry point for DeeFix.
Handles initial scan and real-time monitoring of MP3 files.
"""

import os
import sys
import time
from watchdog.observers import Observer
from .database import init_db
from .processor import process_mp3_file
from .file_utils import is_in_hidden_folder, is_duplicate_and_remove
from .watcher import MP3Handler


def main(folder):
    """Main function for batch processing and monitoring MP3 files.
    
    Performs an initial scan of all MP3 files in the folder,
    displays a summary, then monitors for new files in real-time.
    
    Args:
        folder: Path to the folder to monitor
    """
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
        'duplicates_removed': 0,
        'artwork_fetched': 0,
        'gain_fixed': 0,
        'essentia_analyzed': 0
    }
    
    # Initial scan of all MP3 files
    print("Starting initial scan...", file=sys.stderr)
    # Récupère la liste de tous les fichiers MP3 à traiter
    mp3_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.mp3'):
                # Ignore les fichiers qui commencent par un point
                if os.path.basename(file).startswith('.'):
                    continue
                path = os.path.join(root, file)
                mp3_files.append(path)

    total = len(mp3_files)
    for idx, path in enumerate(mp3_files, 1):
        # Skip hidden folders
        if is_in_hidden_folder(path):
            print(f"File in hidden folder, ignored: {path}", file=sys.stderr)
            stats['hidden_folders'] += 1
            continue

        # Remove duplicates if enabled
        if os.environ.get('REMOVE_DUPLICATES', 'false').lower() == 'true':
            if is_duplicate_and_remove(path):
                stats['duplicates_removed'] += 1
                continue

        stats['total_files'] += 1
        print(f"{idx}/{total} : {os.path.basename(path)}", file=sys.stderr)
        process_mp3_file(path, stats)
    
    # Display processing summary
    print("\n" + "-"*80, file=sys.stderr)
    print("PROCESSING SUMMARY", file=sys.stderr)
    print("-"*80, file=sys.stderr)
    print(f"MP3 files analyzed: {stats['total_files']}", file=sys.stderr)
    if stats['isrc_match'] > 0:
        print(f"  ├─ ✓ Tags updated (ISRC found in Deezer): {stats['isrc_match']}", file=sys.stderr)
    if stats['artwork_fetched'] > 0:
        print(f"  ├─ ✓ Artworks generated (cover.webp): {stats['artwork_fetched']}", file=sys.stderr)
    if stats['gain_fixed'] > 0:
        print(f"  ├─ ✓ Gain normalized (loudgain): {stats['gain_fixed']}", file=sys.stderr)
    if stats['essentia_analyzed'] > 0:
        print(f"  ├─ ✓ Essentia analysis generated: {stats['essentia_analyzed']}", file=sys.stderr)
    if stats['no_isrc_in_mp3'] > 0:
        print(f"  ├─ ✗ No ISRC in MP3: {stats['no_isrc_in_mp3']}", file=sys.stderr)
    if stats['no_matching_isrc'] > 0:
        print(f"  ├─ ✗ No matching ISRC in Deezer: {stats['no_matching_isrc']}", file=sys.stderr)
    if stats['no_deezer_results'] > 0:
        print(f"  ├─ ✗ No Deezer results: {stats['no_deezer_results']}", file=sys.stderr)
    if stats['incomplete_tags'] > 0:
        print(f"  ├─ ✗ Incomplete tags (no artist or title): {stats['incomplete_tags']}", file=sys.stderr)
    if stats['already_processed'] > 0:
        print(f"  ├─ Already processed (skipped): {stats['already_processed']}", file=sys.stderr)
    if stats['hidden_folders'] > 0:
        print(f"  ├─ Ignored files (hidden folder): {stats['hidden_folders']}", file=sys.stderr)
    if stats['duplicates_removed'] > 0:
        print(f"  └─ Duplicates removed: {stats['duplicates_removed']}", file=sys.stderr)
    print("-"*80 + "\n", file=sys.stderr)
    
    # Start real-time monitoring
    print("Activating watcher for new MP3 files...", file=sys.stderr)
    print("-"*80 + "\n", file=sys.stderr)
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
    folder = '/music'
    print(f"Monitoring folder: {folder}", file=sys.stderr)
    main(folder)
