import os
import json
import hashlib
from pathlib import Path
import assemblyai as aai

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_cached_transcription(audio_path, api_key=None, cache_dir="./.cache"):
    """
    Transcribes audio using AssemblyAI with word-level timestamps, with caching logic.
    
    Args:
        audio_path: Path to audio file
        api_key: AssemblyAI API key (if None, reads from ASSEMBLYAI_API_KEY env var)
        cache_dir: Directory to cache transcriptions
    
    Returns:
        dict with 'text', 'words', and 'segments' keys
        - 'words': List of dicts with 'text', 'start', 'end', 'confidence'
        - 'segments': List of dicts with 'start', 'end', 'text' (for compatibility)
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
    
    # Get API key
    if api_key is None:
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            raise ValueError("ASSEMBLYAI_API_KEY not found in environment variables")
    
    print(f"Transcribing {audio_path.name} with AssemblyAI...")
    aai.settings.api_key = api_key

    # Configure speech models explicitly (required by latest AssemblyAI SDK)
    # Use routing: try universal-3-pro first (highest accuracy), then universal-2 (broad language support)
    config = aai.TranscriptionConfig(
        speech_models=["universal-3-pro", "universal-2"]
    )

    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(str(audio_path))
    
    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"Transcription failed: {transcript.error}")
    
    # Extract word timestamps (AssemblyAI returns in milliseconds)
    words = []
    for word in transcript.words:
        words.append({
            "text": word.text,
            "start": word.start / 1000.0,  # Convert ms to seconds
            "end": word.end / 1000.0,
            "confidence": word.confidence
        })
    
    # Extract segments (for compatibility with existing code)
    # Use sentences as segments, or create segments from words
    segments = []
    if hasattr(transcript, 'get_sentences'):
        for sentence in transcript.get_sentences():
            segments.append({
                "start": sentence.start / 1000.0,
                "end": sentence.end / 1000.0,
                "text": sentence.text
            })
    else:
        # Fallback: create segments from words (group words into ~5-10 second segments)
        current_segment_words = []
        current_start = None
        segment_duration = 0
        
        for word in words:
            if current_start is None:
                current_start = word["start"]
            
            current_segment_words.append(word)
            segment_duration = word["end"] - current_start
            
            # Create segment when we hit ~8 seconds or end of words
            if segment_duration >= 8.0 or word == words[-1]:
                segments.append({
                    "start": current_start,
                    "end": word["end"],
                    "text": " ".join(w["text"] for w in current_segment_words)
                })
                current_segment_words = []
                current_start = None
    
    # Build result dict (compatible with Whisper format)
    result_dict = {
        "text": transcript.text,
        "words": words,
        "segments": segments,
        "language": transcript.language_code if hasattr(transcript, 'language_code') else "en",
        "duration": words[-1]["end"] if words else 0.0
    }
    
    # Cache the result
    with open(cache_file, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    return result_dict
