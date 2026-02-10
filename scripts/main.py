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
from scripts.llm_assistant import build_prompt, ask_llm, parse_llm_response

def main():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Configuration
    project_root = Path(__file__).parent.parent
    video_path = project_root / "video" / "ffmpeg.mp4"
    audio_dir = project_root / "audio"
    cache_dir = project_root / ".cache"
    
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

    # 5. Q&A Loop (or single question for demo)
    query = "Give the most important points of the transcript with timestamps"
    n_answers = 3
    print(f"Query: {query}")
    print(f"Requesting up to {n_answers} answers...")
    
    retrieved = retrieve_chunks(query, index, embeddings, client)
    prompt = build_prompt(query, retrieved, n_answers=n_answers)
    raw_answer = ask_llm(prompt, client)
    answers = parse_llm_response(raw_answer)
    
    print(f"\n--- {len(answers)} Answer(s) Found ---\n")
    for i, ans in enumerate(answers, 1):
        start = ans.get('start_time')
        end = ans.get('end_time')
        timestamp = f"[{start}s – {end}s]" if start is not None else "[No timestamp]"
        print(f"Answer {i}: {timestamp}")
        print(f"  {ans['answer']}")
        if ans.get('relevance'):
            print(f"  Relevance: {ans['relevance']}")
        print()

if __name__ == "__main__":
    main()
