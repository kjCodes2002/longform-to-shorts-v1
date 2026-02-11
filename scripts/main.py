import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Import modular components
from scripts.audio_processor import get_extracted_audio
from scripts.transcriber import get_cached_transcription
from scripts.rag_engine import (
    chunk_transcript, 
    get_cached_embeddings, 
    setup_faiss_index, 
    retrieve_chunks
)
from scripts.llm_assistant import build_prompt, ask_llm, get_multiple_answers
from scripts.timestamp_parser import parse_timestamps
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
        segments = transcription_data.get('segments', [])
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return

    # 3. Chunking & Embeddings
    print("Processing transcript chunks and embeddings...")
    chunks = chunk_transcript(segments)
    embeddings = get_cached_embeddings(chunks, audio_path, client, str(cache_dir))
    
    # 4. Setup RAG Index
    index = setup_faiss_index(embeddings)

    # 5. Q&A with multiple answer compilations
    query = "Give the most important points of the transcript with timestamps"
    n_answers = 3
    print(f"Query: {query}")
    print(f"Generating {n_answers} answer compilations...\n")
    
    retrieved = retrieve_chunks(query, index, embeddings, client)
    prompt = build_prompt(query, retrieved)
    answers = get_multiple_answers(prompt, client, n_answers=n_answers)
    
    for i, answer in enumerate(answers, 1):
        print(f"{'='*60}")
        print(f"  ANSWER {i} of {n_answers}")
        print(f"{'='*60}")
        print(answer)
        print()
        
        # 6. Extract timestamps and clip video
        print(f"Parsing timestamps for Answer {i}...")
        segments = parse_timestamps(answer)
        
        if segments:
            output_file = clipped_dir / f"answer_{i}_highlight.mp4"
            print(f"Creating highlight video: {output_file.name}")
            try:
                clip_video_segments(str(video_path), segments, str(output_file))
                print(f"Successfully saved {output_file.name}")
            except Exception as e:
                print(f"Error creating highlight video {i}: {e}")
        else:
            print(f"No timestamps found in Answer {i}. Skipping clipping.")
        print()

if __name__ == "__main__":
    main()
