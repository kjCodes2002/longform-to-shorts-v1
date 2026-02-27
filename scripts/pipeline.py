"""
Reusable async pipeline function for the Longform-to-Shorts workflow.
Can be called from both CLI (main.py) and API (server/routes/pipeline.py).
"""

import os
import logging
from pathlib import Path
from openai import AsyncOpenAI

from scripts.audio_processor import get_extracted_audio
from scripts.transcriber import get_cached_transcription
from scripts.llm_assistant import build_prompt, get_multiple_answers_async
from scripts.segment_matcher import extract_lines_from_answer, match_lines_to_segments, merge_overlapping_segments
from scripts.video_clipper import clip_video_segments

logger = logging.getLogger(__name__)


async def run_pipeline(
    video_path: str,
    n_answers: int = 1,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> dict:
    """
    Run the full longform-to-shorts pipeline.

    Args:
        video_path: Path to the source video file (absolute or relative to project root).
        n_answers: Number of highlight sets to generate.
        model: OpenAI model to use.
        temperature: LLM temperature for generation.

    Returns:
        dict with keys:
            - status: "ok" or "error"
            - clips: list of dicts with "path" and "segments" for each generated clip
            - errors: list of error strings (if any)
    """
    project_root = Path(__file__).parent.parent
    video_path_obj = Path(video_path)

    # Resolve relative paths against project root
    if not video_path_obj.is_absolute():
        video_path_obj = project_root / video_path_obj

    audio_dir = project_root / "audio"
    cache_dir = project_root / ".cache"
    clipped_dir = project_root / "clipped"

    result = {"status": "ok", "clips": [], "errors": []}

    if not video_path_obj.exists():
        return {"status": "error", "clips": [], "errors": [f"Video file not found: {video_path_obj}"]}

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 1. Extract Audio
    try:
        logger.info(f"Extracting audio from {video_path_obj.name}...")
        audio_path = get_extracted_audio(str(video_path_obj), str(audio_dir))
    except Exception as e:
        return {"status": "error", "clips": [], "errors": [f"Error extracting audio: {e}"]}

    # 2. Transcribe
    try:
        logger.info("Starting transcription...")
        transcription_data = get_cached_transcription(audio_path, api_key=None, cache_dir=str(cache_dir))
        whisper_segments = transcription_data.get("segments") or []
        words = transcription_data.get("words") or []
        logger.info(f"Transcription complete: {len(whisper_segments)} segments, {len(words)} words")
    except Exception as e:
        return {"status": "error", "clips": [], "errors": [f"Error transcribing audio: {e}"]}

    # 3. Prepare Full Transcript
    full_transcript = "\n".join([seg['text'].strip() for seg in whisper_segments])

    # 4. Extract Key Moments (Parallel)
    logger.info(f"Generating {n_answers} Key Moments set(s) using {model}...")
    prompt = build_prompt(full_transcript)
    highlight_sets = await get_multiple_answers_async(
        prompt, client, n_answers=n_answers, model=model, temperature=temperature
    )

    # 5. Process each highlight set
    for i, highlights in enumerate(highlight_sets, 1):
        logger.info(f"Processing Highlight Set {i}: {len(highlights)} segments found")

        lines = extract_lines_from_answer(highlights)

        if not lines:
            logger.warning(f"No text lines found in Set {i}. Skipping.")
            result["errors"].append(f"No text lines found in Set {i}")
            continue

        logger.debug(f"Matching lines to transcript for Set {i}...")
        matched = match_lines_to_segments(lines, whisper_segments, words=words)

        if matched:
            logger.info(f"  Matched {len(matched)} fragments. Merging overlaps...")
            raw_segments = [(start, end) for start, end, _ in matched]
            merged_segments = merge_overlapping_segments(raw_segments)

            output_file = clipped_dir / f"highlight_set_{i}.mp4"
            logger.info(f"Creating highlight video: {output_file.name}")
            try:
                clip_video_segments(str(video_path_obj), merged_segments, str(output_file))
                logger.info(f"✅ Successfully saved {output_file.name}")
                result["clips"].append({
                    "path": str(output_file),
                    "segments": [{"start": s, "end": e} for s, e in merged_segments],
                })
            except Exception as e:
                error_msg = f"Error creating highlight video {i}: {e}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
        else:
            logger.warning(f"No segments matched for Set {i}.")
            result["errors"].append(f"No segments matched for Set {i}")

    if not result["clips"] and result["errors"]:
        result["status"] = "error"

    return result
