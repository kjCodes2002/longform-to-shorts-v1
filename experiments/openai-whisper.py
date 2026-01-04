from openai import OpenAI
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

openaiClient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("./audio/audio2.m4a", "rb") as audio_file:
    result = openaiClient.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="verbose_json"
    )

transcript = ""

for segment in result.segments:
    start = segment.start
    end = segment.end
    text = segment.text
    transcript += f"[{start:.2f} → {end:.2f}] {text}\n"

geminiClient = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are an expert content analyst and editor.

You will be given a transcript consisting of multiple lines, each with a timestamp and spoken text.

Your task is to:

Understand the overall context and topic of the transcript.

Identify the most important, insightful, or value-dense lines from the transcript — the parts that best capture the core ideas, arguments, or takeaways.

Select only the minimal set of lines that are sufficient to convey the most valuable essence of the transcript.

Selection rules:

Choose lines that contain key ideas, conclusions, insights, or turning points.

Prefer substance over filler, repetition, anecdotes, or small talk.

Preserve the original wording and timestamps exactly as given.

Do not paraphrase or rewrite selected lines.

Do not invent or infer timestamps.

Output format:

First, provide a brief 2–3 sentence summary describing the overall context/topic.

Then, list the selected transcript lines, each on a new line, in chronological order, keeping their original timestamps.

Constraints:

Be selective: fewer, high-value lines are better than many mediocre ones.

The selected lines should be sufficient for someone to understand the core message without reading the full transcript.

Do not include any lines outside the provided transcript.

Your goal is to extract signal from noise and surface the most meaningful parts of the conversation."""

response = geminiClient.models.generate_content(
    model="gemini-2.5-flash",
    contents=[transcript],
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.5,
    )
)

print(response.text)