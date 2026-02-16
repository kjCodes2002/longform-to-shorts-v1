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
- Format as a bulleted list using "- " prefix.
"""

def ask_llm(prompt, client, model="gpt-4o-mini", temperature=0.7):
    """Sends prompt to OpenAI Chat API."""
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def get_multiple_answers(prompt, client, n_answers=3, model="gpt-4o-mini", temperature=0.7):
    """
    Calls the LLM n_answers times with temperature to generate
    diverse, full-length answers for the user to compare.
    """
    answers = []
    for i in range(n_answers):
        print(f"  Generating answer {i + 1}/{n_answers}...")
        answer = ask_llm(prompt, client, model=model, temperature=temperature)
        answers.append(answer)
    return answers
