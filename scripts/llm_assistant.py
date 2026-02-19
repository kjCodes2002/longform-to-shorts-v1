import asyncio
import json

def build_prompt(transcript_text):
    """Constructs the prompt for extracting key moments from the full transcript."""
    return f"""
You are an expert video editor and content strategist. Your task is to identify the most engaging, interesting, and viral-worthy moments from the provided transcript.

Transcript:
{transcript_text}

Instructions:
- Identify 3-5 distinct "Key Moments" or "Highlights".
- These should be standalone segments that are funny, insightful, surprising, or highly engaging.
- For each moment, provide the EXACT VERBATIM text from the transcript.
- DO NOT paraphrase, summarize, or modify the transcript text in any way.
- DO NOT include timestamps.

Return the result as a JSON object with a 'highlights' key containing a list of strings.
Example:
{{
  "highlights": [
    "verbatim text line 1",
    "verbatim text line 2"
  ]
}}
"""

async def ask_llm_async(prompt, client, model="gpt-4o-mini", temperature=0.7):
    """Sends prompt to OpenAI Chat API asynchronously with JSON mode."""
    response = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
            {"role": "user", "content": prompt}
        ]
    )
    content = response.choices[0].message.content
    try:
        return json.loads(content).get("highlights", [])
    except json.JSONDecodeError:
        print(f"Error decoding JSON from LLM: {content}")
        return []

async def get_multiple_answers_async(prompt, client, n_answers=3, model="gpt-4o-mini", temperature=0.7):
    """
    Calls the LLM n_answers times in parallel using asyncio.
    """
    tasks = []
    for i in range(n_answers):
        tasks.append(ask_llm_async(prompt, client, model=model, temperature=temperature))
    
    print(f"  Generating {n_answers} highlight sets in parallel...")
    results = await asyncio.gather(*tasks)
    return results

# Keep synchronous versions for backward compatibility if needed, 
# but they will just wrap the async ones for simplicity in this transition
def ask_llm(prompt, client, model="gpt-4o-mini", temperature=0.7):
    import asyncio
    return asyncio.run(ask_llm_async(prompt, client, model, temperature))

def get_multiple_answers(prompt, client, n_answers=1, model="gpt-4o-mini", temperature=0.7):
    import asyncio
    return asyncio.run(get_multiple_answers_async(prompt, client, n_answers, model, temperature))
