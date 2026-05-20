"""
Audiomuse-AI integration for triggering a global rescan after MP3 processing.
Uses a debounce timer to coalesce rapid calls into a single HTTP request.
"""

import sys
import threading
import requests
from .config import get_processing_options

_rescan_timer = None
_rescan_lock = threading.Lock()


def schedule_global_rescan():
    """Schedule a debounced global rescan on audiomuse-ai.

    Multiple calls within the debounce window collapse into a single HTTP request.
    Errors are logged but never propagate to the caller.
    """
    options = get_processing_options()
    if not options.get('call_audiomuse') or not options.get('audiomuse_url'):
        return

    global _rescan_timer
    delay = options['audiomuse_debounce']

    with _rescan_lock:
        if _rescan_timer is not None:
            _rescan_timer.cancel()
        _rescan_timer = threading.Timer(delay, _trigger_global_rescan)
        _rescan_timer.daemon = True
        _rescan_timer.start()

    print(f"Audiomuse-AI rescan scheduled in {delay}s", file=sys.stderr)


def _trigger_global_rescan():
    options = get_processing_options()
    url = options['audiomuse_url'] + '/api/analysis/start'
    try:
        response = requests.post(
            url,
            json={"num_recent_albums": 10, "top_n_moods": 15},
            timeout=30,
        )
        response.raise_for_status()
        print(f"Audiomuse-AI rescan triggered: {url} -> HTTP {response.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"Audiomuse-AI rescan failed ({url}): {e}", file=sys.stderr)
