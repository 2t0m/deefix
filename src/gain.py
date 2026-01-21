"""
Gain normalization using loudgain.
Applies ReplayGain tags to MP3 files without modifying audio.
"""

import sys
import subprocess


def fix_gain(file_path, stats=None):
    """Apply loudgain normalization to an MP3 file.
    
    Uses loudgain with --tagmode=i to add ReplayGain tags without modifying audio.
    
    Args:
        file_path: Path to the MP3 file
        stats: Statistics dictionary (optional)
        
    Returns:
        True if gain was applied successfully, False otherwise
    """
    try:
        print(f"Applying loudgain to: {file_path}", file=sys.stderr)
        result = subprocess.run(
            ['loudgain', '--tagmode=i', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Loudgain applied successfully", file=sys.stderr)
        if stats:
            stats['gain_fixed'] += 1
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error applying loudgain: {e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: loudgain command not found. Please install loudgain.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error applying loudgain: {e}", file=sys.stderr)
        return False
