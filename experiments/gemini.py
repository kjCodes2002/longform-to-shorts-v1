from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import whisper

load_dotenv()

# model = whisper.load_model("turbo")

# result = model.transcribe("./audio/audio2.m4a", fp16=False)

# transcript = ""

# for segment in result["segments"]:
#     start = segment["start"]
#     end = segment["end"]
#     text = segment["text"]
#     transcript += f"[{start:.2f} → {end:.2f}] {text}\n"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

transcript = """[0.00 → 5.00]  Do you have a long list of goals, desires and wants for your life?
[5.00 → 11.00]  Do you want to learn more, improve your skills, get the most out of your relationships, live better?
[11.00 → 15.00]  All those things are good. Life is about moving forward and making consistent progress.
[15.00 → 21.00]  However, there is one important thing in all this working, hustling, striving and achieving more.
[21.00 → 25.00]  You can't do everything at the same time. Just common sense right?
[25.00 → 32.00]  You only have so much time and energy. So if you take on too many things, you end up spread too thin.
[32.00 → 36.00]  Instead, it's just more effective to focus your effort on one thing.
[36.00 → 41.00]  Success adds up. Real success happens when you focus on one thing at a time.
[41.00 → 44.00]  The first time I discovered that idea was in high school.
[44.00 → 48.00]  When I was preparing for my final exams, I decided to study only one subject at a time.
[48.00 → 52.00]  And I only moved on to the next when I fully grasped the material.
[52.00 → 57.00]  I noticed that I could learn something way faster if I immersed myself in it for a few days.
[57.00 → 62.00]  Most of my peers studied multiple subjects a day. I never liked their approach because it's too scattered.
[62.00 → 66.00]  If I'm working on a project at work, I don't pick up another big project.
[66.00 → 70.00]  If I'm working on a new course for my blog, I don't start writing a book at the same time.
[70.00 → 73.00]  That strategy helps me get things done quicker and better.
[73.00 → 77.00]  Hence, I achieve much more when I give my attention to one thing.
[77.00 → 83.00]  Gary Keller and Jay Paperson, authors of the one thing, which is a great book about his same concept said it best.
[83.00 → 88.00]  When I had fewer success, I had narrowed my concentration to one thing.
[88.00 → 91.00]  And while my success varied, my focus had two.
[91.00 → 95.00]  Are you working on a lot of things? Is your attention not on one thing?
[95.00 → 99.00]  There's a big chance that you will not achieve the best possible results.
[99.00 → 103.00]  Or worse, you might fail if you try to achieve many things at the same time.
[103.00 → 107.00]  The reason is simple. Most of us believe that success happens all at once.
[107.00 → 110.00]  Real life is different. KLA and Typeson put it well.
[110.00 → 112.00]  Success is sequential, not simultaneous."""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[transcript],
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.3,
    )
)

print(response.text)