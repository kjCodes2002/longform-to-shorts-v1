import os
import json
import hashlib
from pathlib import Path

def get_file_hash(filepath):
    """Generates an MD5 hash of a file's content."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def get_cached_transcription(audio_path, client, cache_dir="./.cache"):
    """
    Transcribes audio using OpenAI Whisper, with caching logic.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    file_hash = get_file_hash(audio_path)
    cache_file = Path(cache_dir) / f"transcription_{file_hash}.json"
    
    if cache_file.exists():
        print(f"Loading cached transcription for {audio_path.name}...")
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    print(f"Transcribing {audio_path.name} with Whisper...")
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json"
        )
        # Convert response to dict for JSON serialization
        result_dict = response.model_dump()
        with open(cache_file, 'w') as f:
            json.dump(result_dict, f)
        return result_dict
