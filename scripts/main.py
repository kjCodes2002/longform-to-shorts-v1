import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Import modular components
from scripts.audio_processor import get_extracted_audio
from scripts.transcriber import get_cached_transcription
from scripts.llm_assistant import build_prompt, ask_llm, get_multiple_answers
from scripts.segment_matcher import extract_lines_from_answer, match_lines_to_segments, merge_overlapping_segments
from scripts.video_clipper import clip_video_segments

def main():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Configuration
    project_root = Path(__file__).parent.parent
    video_path = project_root / "video" / "ffmpeg.mp4"
    audio_dir = project_root / "audio"
    cache_dir = project_root / ".cache"
    clipped_dir = project_root / "clipped"
    
    print(f"--- Starting Orchestrator ---")
    
    # 1. Extract Audio
    try:
        audio_path = get_extracted_audio(str(video_path), str(audio_dir))
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return

    # 2. Transcribe
    try:
        transcription_data = get_cached_transcription(audio_path, client, str(cache_dir))
        whisper_segments = transcription_data.get("segments") or []
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return

    # 3. Prepare Full Transcript
    print("Preparing full transcript for LLM...")
    full_transcript = "\n".join([seg['text'].strip() for seg in whisper_segments])
    
    # 4. Extract Key Moments
    n_answers = 1  # Generate 1 set of key moments by default, or more if specific variety needed
    print(f"Generating Key Moments suggestions...\n")
    
    prompt = build_prompt(full_transcript)
    answers = get_multiple_answers(prompt, client, n_answers=n_answers)
    
    for i, answer in enumerate(answers, 1):
        print(f"{'='*60}")
        print(f"  KEY MOMENTS SET {i}")
        print(f"{'='*60}")
        print(answer)
        print()
        
        # 5. Extract verbatim lines from LLM output
        lines = extract_lines_from_answer(answer)
        
        if not lines:
            print(f"No text lines found in Answer {i}. Skipping clipping.")
            print()
            continue
        
        # 6. Match lines back to original Whisper segments for precise timestamps
        print(f"Matching {len(lines)} lines to original Whisper segments...")
        matched = match_lines_to_segments(lines, whisper_segments)
        if matched:
            print(f"  Matched {len(matched)} segments (before merging):")
            for start, end, text in matched:
                print(f"    [{start} -> {end}] {text.strip()}")
        
        if matched:
            # Convert to (start, end) tuples and merge overlapping segments
            raw_segments = [(start, end) for start, end, _ in matched]
            merged_segments = merge_overlapping_segments(raw_segments)
            
            # Log the merged timestamps
            print(f"  Merged {len(raw_segments)} matches into {len(merged_segments)} non-overlapping segments:")
            for start, end in merged_segments:
                print(f"    [{start} -> {end}]")
            
            output_file = clipped_dir / f"highlight_set_{i}.mp4"
            print(f"Creating highlight video: {output_file.name}")
            try:
                clip_video_segments(str(video_path), merged_segments, str(output_file))
                print(f"Successfully saved {output_file.name}")
            except Exception as e:
                print(f"Error creating highlight video {i}: {e}")
        else:
            print(f"No segments matched for Answer {i}. Skipping clipping.")
        print()

if __name__ == "__main__":
    main()
