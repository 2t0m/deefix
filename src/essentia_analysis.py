import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
# --- TensorFlow-based Essentia analysis and tag writing ---
import sys
import os
import json
import numpy as np
from essentia.standard import MonoLoader, TensorflowPredictEffnetDiscogs, TensorflowPredict2D
import essentia
from .mp3_tags import set_mp3_tag

# Model directory and files (adapt as needed)
MODEL_DIR = os.path.expanduser('~/essentia_models')
EMBEDDING_MODEL = f"{MODEL_DIR}/discogs-effnet-bs64-1.pb"
GENRE_MODEL = f"{MODEL_DIR}/genre_discogs400-discogs-effnet-1.pb"
GENRE_METADATA = f"{MODEL_DIR}/genre_discogs400-discogs-effnet-1.json"
MOOD_MODEL = f"{MODEL_DIR}/mtg_jamendo_moodtheme-discogs-effnet-1.pb"
MOOD_METADATA = f"{MODEL_DIR}/mtg_jamendo_moodtheme-discogs-effnet-1.json"

# Configurable thresholds
GENRE_THRESHOLD = 0.15  # 15%
MOOD_THRESHOLD = 0.005  # 0.5%
TOP_N_GENRES = 3
TOP_N_MOODS = 3
GENRE_FORMAT = 'parent_child'  # 'parent_child', 'child_parent', 'child_only', 'raw'

def format_genre_tag(raw_genre, style='parent_child'):
    if style == 'raw':
        return raw_genre
    if '---' in raw_genre:
        parts = raw_genre.split('---')
        parent = parts[0].strip()
        child = parts[1].strip() if len(parts) > 1 else ''
        if style == 'parent_child':
            return f"{parent} - {child}" if child else parent
        elif style == 'child_parent':
            return f"{child} - {parent}" if child else parent
        elif style == 'child_only':
            return child if child else parent
    return raw_genre

def format_mood_tag(raw_mood):
    return raw_mood.title()

def _analyze_with_python_essentia(file_path):
    # Disable Essentia logging to avoid cluttering output
    try:
        if hasattr(essentia, 'log'):
            essentia.log.infoActive = False
            essentia.log.warningActive = False
    except Exception:
        pass
    """Run analysis with python-essentia and return a nested feature dictionary."""
    try:
        # Load models
        embedding_model = TensorflowPredictEffnetDiscogs(graphFilename=EMBEDDING_MODEL, output="PartitionedCall:1")
        genre_model = TensorflowPredict2D(graphFilename=GENRE_MODEL, input="serving_default_model_Placeholder", output="PartitionedCall")
        with open(GENRE_METADATA, 'r') as f:
            genre_labels = json.load(f)['classes']
        mood_model = TensorflowPredict2D(graphFilename=MOOD_MODEL, input="model/Placeholder", output="model/Sigmoid")
        with open(MOOD_METADATA, 'r') as f:
            mood_labels = json.load(f)['classes']
    except Exception as error:
        print(f"[Essentia] Model loading failed: {error}", file=sys.stderr)
        return None
    try:
        audio = MonoLoader(filename=str(file_path), sampleRate=16000, resampleQuality=4)()
        embeddings = embedding_model(audio)
        # GENRE
        genre_predictions = genre_model(embeddings)
        genre_activations = np.mean(genre_predictions, axis=0)
        top_indices = np.argsort(genre_activations)[::-1][:TOP_N_GENRES * 2]
        genres = []
        for idx in top_indices:
            if len(genres) >= TOP_N_GENRES:
                break
            if genre_activations[idx] >= GENRE_THRESHOLD:
                genres.append({'label': genre_labels[idx], 'confidence': float(genre_activations[idx])})
        if not genres:
            top_idx = np.argmax(genre_activations)
            genres.append({'label': genre_labels[top_idx], 'confidence': float(genre_activations[top_idx])})
        formatted_genres = [format_genre_tag(g['label'], style=GENRE_FORMAT) for g in genres]
        # MOOD
        mood_predictions = mood_model(embeddings)
        mood_activations = np.mean(mood_predictions, axis=0)
        moods = []
        for idx, activation in enumerate(mood_activations):
            if activation >= MOOD_THRESHOLD:
                moods.append({'label': mood_labels[idx], 'confidence': float(activation)})
        moods = sorted(moods, key=lambda x: x['confidence'], reverse=True)[:TOP_N_MOODS]
        formatted_moods = [format_mood_tag(m['label']) for m in moods]
        return {
            'genres': genres,
            'formatted_genres': formatted_genres,
            'moods': moods,
            'formatted_moods': formatted_moods,
        }
    except Exception as error:
        print(f"[Essentia] Analysis failed: {error}", file=sys.stderr)
        return None

def analyze_with_essentia(file_path, stats=None):
    print(f"Running Python Essentia analysis on: {file_path}", file=sys.stderr)
    analysis = _analyze_with_python_essentia(file_path)
    if analysis is None:
        print("[Essentia] Analysis failed.", file=sys.stderr)
        return False

    # Write tags using your mp3_tags system

    # Écrase le tag genre avec les genres Essentia uniquement
    if analysis.get('formatted_genres'):
        set_mp3_tag(file_path, 'genre', "; ".join(analysis['formatted_genres']))

    # Integrate Essentia moods with existing ones (without duplicates)
    if analysis.get('formatted_moods'):
        from .mp3_tags import get_mp3_tags
        tags, *_ = get_mp3_tags(file_path)
        existing_moods = tags.get('mood', [])
        existing_moods = [m.strip() for val in existing_moods for m in val.split(',') if m.strip()]
        all_moods = existing_moods + analysis['formatted_moods']
        seen = set()
        merged_moods = [m for m in all_moods if not (m in seen or seen.add(m))]
        set_mp3_tag(file_path, 'mood', "; ".join(merged_moods))

    if stats is not None and 'essentia_analyzed' in stats:
        stats['essentia_analyzed'] += 1

    print("Essentia analysis completed and ID3 tags updated", file=sys.stderr)
    return True
