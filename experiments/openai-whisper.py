from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("./audio/audio2.m4a", "rb") as audio_file:
    result = client.audio.transcriptions.create(
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

print(transcript)