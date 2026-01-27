import os
import json
import hashlib
from dotenv import load_dotenv
import tiktoken
import faiss
import numpy as np
from openai import OpenAI

load_dotenv()

openaiClient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

AUDIO_PATH = "./audio/audio2.m4a"
CACHE_DIR = "./.cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def get_cached_transcription(audio_path):
    file_hash = get_file_hash(audio_path)
    cache_file = os.path.join(CACHE_DIR, f"transcription_{file_hash}.json")
    
    if os.path.exists(cache_file):
        print(f"Loading cached transcription for {audio_path}...")
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    print(f"Transcribing {audio_path}...")
    with open(audio_path, "rb") as audio_file:
        response = openaiClient.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json"
        )
        # Convert response to dict for JSON serialization
        result_dict = response.model_dump()
        with open(cache_file, 'w') as f:
            json.dump(result_dict, f)
        return result_dict

result_data = get_cached_transcription(AUDIO_PATH)
# Wrap result in a SimpleNamespace or dot-accessible object if needed, 
# but here we'll just use dict access or adapt the loop.
# The previous code used result.segments. result_data is a dict now.

class TranscriptChunk:
    def __init__(self, start_time, end_time, text, chunk_index):
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.chunk_index = chunk_index

data = []

encoding = tiktoken.get_encoding("cl100k_base")
def token_count(text: str) -> int:
    return len(encoding.encode(text))

MAX_TOKENS = 150  
OVERLAP_TOKENS = 30
chunk_index = 0

data = []
current_chunks = [] # List of segments in current chunk
current_tokens = 0

segments = result_data.get('segments', [])

i = 0
while i < len(segments):
    segment = segments[i]
    text = segment['text'].strip().replace("\n", " ")
    tokens = token_count(text)
    
    current_chunks.append(segment)
    current_tokens += tokens
    
    # If we exceed MAX_TOKENS, create a chunk and backtrack for overlap
    if current_tokens >= MAX_TOKENS:
        chunk_text = " ".join([s['text'].strip() for s in current_chunks])
        data.append(TranscriptChunk(
            start_time=current_chunks[0]['start'],
            end_time=current_chunks[-1]['end'],
            text=chunk_text,
            chunk_index=len(data)
        ))
        
        # Backtrack logic for overlap: 
        # Find how many segments to keep for next chunk to satisfy OVERLAP_TOKENS
        overlap_count = 0
        overlap_tokens_accum = 0
        for j in range(len(current_chunks) - 1, -1, -1):
            s_tokens = token_count(current_chunks[j]['text'])
            if overlap_tokens_accum + s_tokens <= OVERLAP_TOKENS:
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

# Final chunk
if current_chunks:
    chunk_text = " ".join([s['text'].strip() for s in current_chunks])
    data.append(TranscriptChunk(
        start_time=current_chunks[0]['start'],
        end_time=current_chunks[-1]['end'],
        text=chunk_text,
        chunk_index=len(data)
    ))

print(f"Created {len(data)} chunks with overlap.")

def get_cached_embeddings(chunks, audio_path):
    file_hash = get_file_hash(audio_path)
    cache_file = os.path.join(CACHE_DIR, f"embeddings_{file_hash}.json")
    
    if os.path.exists(cache_file):
        print("Loading cached embeddings...")
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    print(f"Generating embeddings for {len(chunks)} chunks...")
    texts = [c.text for c in chunks]
    # OpenAI supports batching by passing a list of strings
    response = openaiClient.embeddings.create(
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

embeddings = get_cached_embeddings(data, AUDIO_PATH)

vectors = np.array([item["vector"] for item in embeddings], dtype="float32")

dimension = vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(vectors)

# Embedding the user query
def embed_query(query: str):
    response = openaiClient.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return np.array([response.data[0].embedding], dtype="float32")

# Retrieve relevant chunks using FAISS
def retrieve_chunks(query: str, k=4):
    query_vector = embed_query(query)
    distances, indices = index.search(query_vector, k)

    return [embeddings[i] for i in indices[0]]

# Construct a grounded prompt
def build_prompt(query, retrieved_chunks):
    context = ""

    for chunk in retrieved_chunks:
        context += (
            f"[{chunk['start_time']}s – {chunk['end_time']}s]\n"
            f"{chunk['text']}\n\n"
        )

    return f"""
You are an assistant answering questions strictly based on the provided transcript context.

Transcript context:
{context}

Question:
{query}

Instructions:
- Answer ONLY using the transcript context.
- If the answer is not present, say "Not mentioned in the video."
- Be concise and factual.
"""

# Ask the LLM
def ask_llm(prompt):
    response = openaiClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def answer_question(query):
    retrieved = retrieve_chunks(query)
    prompt = build_prompt(query, retrieved)
    return ask_llm(prompt)

print(answer_question("Give the most important points of the transcript with timestamps"))
