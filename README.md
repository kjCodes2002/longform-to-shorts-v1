# 🎥 Longform-to-Shorts (v1)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/API-OpenAI-orange.svg)](https://openai.com/)
[![FFmpeg](https://img.shields.io/badge/Dependency-FFmpeg-green.svg)](https://ffmpeg.org/)

An intelligent pipeline designed to process long-form video content, extract transcriptions, and utilize a **RAG (Retrieval-Augmented Generation)** architecture to identify highlights and answer questions about the content.

---

## 🚀 Overview

This project implements a modular pipeline that transforms raw video files into searchable, semantically-indexed content. It leverages state-of-the-art AI models for transcription and reasoning.

### Key Logic Flow
```mermaid
graph LR
    A[Video File] --> B[FFmpeg]
    B --> C[WAV Audio]
    C --> D[OpenAI Whisper]
    D --> E[JSON Transcript]
    E --> F[Semantic Overlap Chunking]
    F --> G[OpenAI Embeddings]
    G --> H[FAISS Vector Index]
    H --> I[Contextual Q&A / Highlight Extraction]
```

---

## ✨ Features

- **Modular Architecture**: Clean separation of concerns with dedicated modules for audio processing, transcription, RAG, and LLM interaction.
- **Intelligent Caching**: MD5-based file hashing ensures that expensive transcription and embedding steps are only performed when source files change.
- **Advanced RAG Pipeline**:
  - Semantic chunking with overlapping windows to preserve context.
  - FAISS-powered vector search for highly relevant context retrieval.
  - Grounded LLM responses to ensure factual accuracy based on the transcript.
- **Robust Audio Processing**: Professional-grade audio extraction using FFmpeg (16kHz, Mono, PCM-16).

---

## 📁 Project Structure

```text
whisper/
├── scripts/             # Modular pipeline components
│   ├── audio_processor.py   # FFmpeg extraction logic
│   ├── transcriber.py       # Whisper API & caching
│   ├── rag_engine.py        # Chunking, Embeddings, FAISS
│   ├── llm_assistant.py     # Prompt engineering
│   └── main.py              # Orchestrator script
├── experiments/         # Prototyping and earlier iterations
├── video/               # Source video files (ignored by git)
├── audio/               # Extracted audio outputs (ignored by git)
├── .cache/              # Persistent JSON caches for AI outputs
└── .env                 # API keys and environment variables
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
Ensure you have FFmpeg installed on your system:
```bash
# MacOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg
```

### 2. Environment Setup
Create a virtual environment and install dependencies:
```bash
python3 -m venv myenv
source myenv/bin/activate
pip install openai tiktoken faiss-cpu numpy python-dotenv
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_actual_key_here
```

---

## 📖 Usage

Place your video file in the `video/` directory (e.g., `ffmpeg.mp4`) and run the main orchestrator:

```bash
python3 -m scripts.main
```

The script will:
1. Extract audio from the video.
2. Transcribe it (or load from cache).
3. Index the transcript semantically.
4. Answer a sample query based on the video content.

---

## 🚧 Status

Currently in **Beta**. The core RAG pipeline is stable, while highlight extraction and short-form clip generation are under active development.
