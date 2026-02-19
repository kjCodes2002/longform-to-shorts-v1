import os
import asyncio
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Import modular components
from scripts.audio_processor import get_extracted_audio
from scripts.transcriber import get_cached_transcription
from scripts.llm_assistant import build_prompt, get_multiple_answers_async
from scripts.segment_matcher import extract_lines_from_answer, match_lines_to_segments, merge_overlapping_segments
from scripts.video_clipper import clip_video_segments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Longform-to-Shorts Video Pipeline")
    parser.add_argument("--video", type=str, help="Path to source video", default="video/ffmpeg.mp4")
    parser.add_argument("--n_answers", type=int, help="Number of highlight sets to generate", default=1)
    parser.add_argument("--model", type=str, help="OpenAI model to use", default="gpt-4o-mini")
    parser.add_argument("--temperature", type=float, help="LLM temperature", default=0.7)
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Configuration
    project_root = Path(__file__).parent.parent
    video_path = project_root / args.video
    audio_dir = project_root / "audio"
    cache_dir = project_root / ".cache"
    clipped_dir = project_root / "clipped"
    
    logger.info("--- Starting Orchestrator ---")
    
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return

    # 1. Extract Audio
    try:
        logger.info(f"Extracting audio from {video_path.name}...")
        audio_path = get_extracted_audio(str(video_path), str(audio_dir))
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return

    # 2. Transcribe
    try:
        logger.info("Starting transcription...")
        transcription_data = get_cached_transcription(audio_path, api_key=None, cache_dir=str(cache_dir))
        whisper_segments = transcription_data.get("segments") or []
        words = transcription_data.get("words") or []
        logger.info(f"Transcription complete: {len(whisper_segments)} segments, {len(words)} words")
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return

    # 3. Prepare Full Transcript
    full_transcript = "\n".join([seg['text'].strip() for seg in whisper_segments])
    
    # 4. Extract Key Moments (Parallel)
    logger.info(f"Generating {args.n_answers} Key Moments set(s) using {args.model}...")
    prompt = build_prompt(full_transcript)
    highlight_sets = await get_multiple_answers_async(
        prompt, client, n_answers=args.n_answers, model=args.model, temperature=args.temperature
    )
    
    for i, highlights in enumerate(highlight_sets, 1):
        logger.info(f"Processing Highlight Set {i}: {len(highlights)} segments found")
        
        # 5. Extract and clean lines
        lines = extract_lines_from_answer(highlights)
        
        if not lines:
            logger.warning(f"No text lines found in Set {i}. Skipping.")
            continue
        
        # 6. Match lines for precise timestamps
        logger.debug(f"Matching lines to transcript for Set {i}...")
        matched = match_lines_to_segments(lines, whisper_segments, words=words)
        
        if matched:
            logger.info(f"  Matched {len(matched)} fragments. Merging overlaps...")
            raw_segments = [(start, end) for start, end, _ in matched]
            merged_segments = merge_overlapping_segments(raw_segments)
            
            output_file = clipped_dir / f"highlight_set_{i}.mp4"
            logger.info(f"Creating highlight video: {output_file.name}")
            try:
                clip_video_segments(str(video_path), merged_segments, str(output_file))
                logger.info(f"✅ Successfully saved {output_file.name}")
            except Exception as e:
                logger.error(f"Error creating highlight video {i}: {e}")
        else:
            logger.warning(f"No segments matched for Set {i}.")

if __name__ == "__main__":
    asyncio.run(main())
