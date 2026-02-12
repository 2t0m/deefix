"""
MP3 file processor.
Orchestrates the processing of MP3 files including tag fixing, artwork generation, and gain normalization.
"""

import sys
from .config import get_processing_options
from .database import is_file_processed, update_file_processing_status
from .mp3_tags import get_mp3_tags, check_tags, set_mp3_tag, get_audio_duration
from .artwork import fetch_video_artwork
from .deezer_api import search_deezer_track, get_deezer_track_info
from .lyrics import search_lrclib_lyrics
from .gain import fix_gain


def handle_stats(stats, key):
    """Increment a statistics counter if stats dict is provided.
    
    Args:
        stats: Statistics dictionary (can be None)
        key: Key to increment
    """
    if stats:
        stats[key] += 1


def process_mp3_file(file_path, stats=None):
    """Orchestrate the processing of a single MP3 file.
    
    Processing steps:
    1. Check if already processed (early exit)
    2. Read and validate tags
    3. Optionally generate artwork from Apple Music
    4. Search Deezer for track info
    5. Update tags if ISRC matches
    6. Optionally apply loudgain normalization
    
    Args:
        file_path: Path to the MP3 file
        stats: Statistics dictionary to update (optional)
        
    Returns:
        Status string: 'already_processed', 'incomplete_tags', 'no_deezer_results',
                      'isrc_match', 'no_isrc_in_mp3', 'no_matching_isrc', or 'fix_tags_skipped'
    """
    # Step 1: Check if already processed and what needs to be done
    processed_status = is_file_processed(file_path)
    options = get_processing_options()
    
    # Track what was done in this run
    processing_done = {
        'tags_fixed': False,
        'lyrics_fetched': False,
        'artwork_generated': False,
        'gain_applied': False
    }
    
    # Determine what still needs processing
    skip_tags = processed_status and processed_status['tags_fixed'] and not options['fix_tags']
    skip_artwork = processed_status and processed_status['artwork_generated']
    skip_gain = processed_status and processed_status['gain_applied']
    
    if processed_status:
        handle_stats(stats, 'already_processed')
        return 'already_processed'
    
    # Step 2: Read and validate tags
    print(f"Reading tags from: {file_path}", file=sys.stderr)
    tags = get_mp3_tags(file_path)[0]
    artist, album, title, has_tags = check_tags(tags)
    print(f"File: {file_path}")
    
    if not has_tags:
        print("Incomplete tags\n")
        handle_stats(stats, 'incomplete_tags')
        return 'incomplete_tags'
    
    # Step 3: Generate artwork if needed and not already done
    if not skip_artwork and options['fetch_video_artwork']:
        artwork_result = fetch_video_artwork(artist, album, title, file_path, stats)
        if artwork_result:
            processing_done['artwork_generated'] = True
    elif processed_status:
        processing_done['artwork_generated'] = processed_status['artwork_generated']
    
    # Step 4: Search Deezer if tags need fixing
    result = 'no_changes'
    if not skip_tags and options['fix_tags']:
        track_ids = search_deezer_track(artist, album, title)
        if not track_ids:
            print("No Deezer results\n")
            handle_stats(stats, 'no_deezer_results')
        else:
            # Step 5: Update tags
            result = _update_tags_from_deezer(options, tags, artist, album, title, file_path, track_ids, stats)
            if result == 'isrc_match':
                processing_done['tags_fixed'] = True
                # Check if lyrics were fetched during tag update
                if options['fetch_lyrics']:
                    processing_done['lyrics_fetched'] = True
    elif processed_status:
        processing_done['tags_fixed'] = processed_status['tags_fixed']
        processing_done['lyrics_fetched'] = processed_status['lyrics_fetched']
    
    # Step 6: Apply loudgain if needed and not already done
    if not skip_gain and options['fix_gain']:
        gain_result = fix_gain(file_path, stats)
        if gain_result:
            processing_done['gain_applied'] = True
    elif processed_status:
        processing_done['gain_applied'] = processed_status['gain_applied']
    
    # Update database with processing status
    update_file_processing_status(
        file_path,
        tags_fixed=processing_done['tags_fixed'],
        lyrics_fetched=processing_done['lyrics_fetched'],
        artwork_generated=processing_done['artwork_generated'],
        gain_applied=processing_done['gain_applied']
    )
    
    return result


def _update_tags_from_deezer(options, tags, artist, album, title, file_path, track_ids, stats):
    """Update MP3 tags from Deezer info if enabled and ISRC matches.
    
    Searches through Deezer track results to find an ISRC match with the MP3 file.
    If found, updates all tags and optionally fetches lyrics.
    
    Args:
        options: Processing options dictionary
        tags: Current MP3 tags
        artist: Artist name
        album: Album name
        title: Track title
        file_path: Path to the MP3 file
        track_ids: List of Deezer track IDs to check
        stats: Statistics dictionary
        
    Returns:
        Status string: 'isrc_match', 'no_isrc_in_mp3', 'no_matching_isrc', or 'fix_tags_skipped'
    """
    mp3_isrc = tags.get('isrc', [''])[0] if isinstance(tags.get('isrc'), list) else tags.get('isrc', '')
    print(f"MP3 ISRC: '{mp3_isrc}'")
    
    if not options['fix_tags']:
        print("FIX_TAGS is false, skipping tag update.", file=sys.stderr)
        return 'fix_tags_skipped'
    
    # Try to find matching ISRC in Deezer results
    for idx, track_id in enumerate(track_ids, 1):
        info = get_deezer_track_info(track_id)
        if not info:
            continue
        
        # Extract album artist
        album_artist = info.get('album', {}).get('artist', {}).get('name') if info.get('album', {}).get('artist') else None
        if not album_artist:
            album_artist = info.get('artist', {}).get('name')
        
        # Build tags dictionary
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
        
        # Check for ISRC match
        if mp3_isrc and deezer_isrc and mp3_isrc == deezer_isrc:
            print(f"ISRC match found on result {idx}!")
            
            # Update basic tags
            for k in ['album', 'title', 'albumartist', 'discnumber', 'tracknumber', 'genre', 'date', 'gain']:
                val = deezer_tags.get(k)
                if val is not None:
                    set_mp3_tag(file_path, k, val)
            
            # Update contributors as artist
            contributors = [c['name'] for c in info.get('contributors', [])]
            if contributors:
                set_mp3_tag(file_path, 'artist', ', '.join(contributors))
            
            # Fetch lyrics if enabled
            if options['fetch_lyrics']:
                duration = get_audio_duration(file_path)
                lyrics = search_lrclib_lyrics(
                    deezer_tags.get('artist', artist),
                    deezer_tags.get('title', title),
                    deezer_tags.get('album', album),
                    duration
                )
                if lyrics:
                    set_mp3_tag(file_path, 'lyrics', lyrics)
                    print("Lyrics added to MP3 file", file=sys.stderr)
                else:
                    print("No lyrics found on lrclib.net for this track", file=sys.stderr)
            else:
                print("Lyrics fetching disabled (FETCH_LYRICS=false)", file=sys.stderr)
            
            print("Tags updated from Deezer (identical ISRC)\n")
            handle_stats(stats, 'isrc_match')
            return 'isrc_match'
    
    # No matching ISRC found
    if not mp3_isrc:
        print("No ISRC in MP3 file, tags not updated\n")
        handle_stats(stats, 'no_isrc_in_mp3')
        return 'no_isrc_in_mp3'
    else:
        print(f"No matching ISRC found in {len(track_ids)} Deezer results, tags not updated\n")
        handle_stats(stats, 'no_matching_isrc')
        return 'no_matching_isrc'
