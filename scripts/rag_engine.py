import json
import os
from pathlib import Path
import numpy as np
import faiss
import tiktoken
import hashlib

class TranscriptChunk:
    def __init__(self, start_time, end_time, text, chunk_index):
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.chunk_index = chunk_index

def token_count(text: str, encoding_name="cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))

def chunk_transcript(segments, max_tokens=150, overlap_tokens=30):
    """
    Splits transcript segments into overlapping chunks based on token count.
    """
    data = []
    current_chunks = []
    current_tokens = 0
    
    i = 0
    while i < len(segments):
        segment = segments[i]
        text = segment['text'].strip().replace("\n", " ")
        tokens = token_count(text)
        
        current_chunks.append(segment)
        current_tokens += tokens
        
        if current_tokens >= max_tokens:
            chunk_text = " ".join([s['text'].strip() for s in current_chunks])
            data.append(TranscriptChunk(
                start_time=current_chunks[0]['start'],
                end_time=current_chunks[-1]['end'],
                text=chunk_text,
                chunk_index=len(data)
            ))
            
            # Backtrack for overlap
            overlap_count = 0
            overlap_tokens_accum = 0
            for j in range(len(current_chunks) - 1, -1, -1):
                s_tokens = token_count(current_chunks[j]['text'])
                if overlap_tokens_accum + s_tokens <= overlap_tokens:
                    overlap_tokens_accum += s_tokens
                    overlap_count += 1
                else:
                    break
            
            if overlap_count > 0:
                current_chunks = current_chunks[-overlap_count:]
                current_tokens = overlap_tokens_accum
            else:
                current_chunks = []
                current_tokens = 0
        i += 1

    if current_chunks:
        chunk_text = " ".join([s['text'].strip() for s in current_chunks])
        data.append(TranscriptChunk(
            start_time=current_chunks[0]['start'],
            end_time=current_chunks[-1]['end'],
            text=chunk_text,
            chunk_index=len(data)
        ))
    return data

def get_cached_embeddings(chunks, audio_path, client, cache_dir="./.cache"):
    """
    Generates or loads cached embeddings for transcript chunks.
    """
    # Simple hash of audio path for cache identification (better would be segments/content hash)
    path_hash = hashlib.md5(str(audio_path).encode()).hexdigest()
    cache_file = Path(cache_dir) / f"embeddings_{path_hash}.json"
    
    if cache_file.exists():
        print("Loading cached embeddings...")
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    print(f"Generating embeddings for {len(chunks)} chunks...")
    texts = [c.text for c in chunks]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    
    embeddings_data = []
    for i, chunk in enumerate(chunks):
        embeddings_data.append({
            "vector": response.data[i].embedding,
            "text": chunk.text,
            "start_time": chunk.start_time,
            "end_time": chunk.end_time,
            "chunk_index": chunk.chunk_index
        })
    
    with open(cache_file, 'w') as f:
        json.dump(embeddings_data, f)
    
    return embeddings_data

def setup_faiss_index(embeddings):
    """Initializes and returns a FAISS index from embeddings."""
    vectors = np.array([item["vector"] for item in embeddings], dtype="float32")
    dimension = vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors)
    return index

def retrieve_chunks(query, index, embeddings, client, k=4):
    """Retrieves context chunks for a given query."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = np.array([response.data[0].embedding], dtype="float32")
    distances, indices = index.search(query_vector, k)
    return [embeddings[i] for i in indices[0]]
