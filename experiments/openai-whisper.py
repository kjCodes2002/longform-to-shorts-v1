from openai import OpenAI
import os
from dotenv import load_dotenv
import tiktoken
import faiss
import numpy as np

load_dotenv()

openaiClient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("./audio/audio2.m4a", "rb") as audio_file:
    result = openaiClient.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="verbose_json"
    )

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

MAX_TOKENS = 100  
chunk_index = 0

current_text = ""
current_tokens = 0
chunk_start_time = None
chunk_end_time = None

for segment in result.segments:
    start = segment.start
    end = segment.end
    text = segment.text.strip().replace("\n", " ")
    segment_tokens = token_count(text)

    if chunk_start_time is None:
        chunk_start_time = start

    if current_tokens + segment_tokens <= MAX_TOKENS:
        current_text += " " + text if current_text else text
        current_tokens += segment_tokens
        chunk_end_time = end
    else:
        data.append(
            TranscriptChunk(
                start_time=chunk_start_time,
                end_time=chunk_end_time,
                text=current_text.strip(),
                chunk_index=chunk_index
            )
        )

        chunk_index += 1

        current_text = text
        current_tokens = segment_tokens
        chunk_start_time = start
        chunk_end_time = end

if current_text:
    data.append(
        TranscriptChunk(
            start_time=chunk_start_time,
            end_time=chunk_end_time,
            text=current_text.strip(),
            chunk_index=chunk_index
        )
    )

embeddings = []

for chunk in data:
    response = openaiClient.embeddings.create(
        model="text-embedding-3-small",
        input=chunk.text
    )

    vector = response.data[0].embedding

    embeddings.append({
        "vector": vector,
        "text": chunk.text,
        "start_time": chunk.start_time,
        "end_time": chunk.end_time,
        "chunk_index": chunk.chunk_index
    })

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
        model="gpt-4.1-mini",
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

print(answer_question("What is the speaker talking about?"))
