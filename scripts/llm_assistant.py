def build_prompt(query, retrieved_chunks):
    """Constructs the augmented prompt for the LLM."""
    context = ""
    for chunk in retrieved_chunks:
        # Use per-segment timestamps if available, otherwise fall back to chunk-level
        if chunk.get('segments'):
            for seg in chunk['segments']:
                context += f"[{seg['start']:.1f}s – {seg['end']:.1f}s] {seg['text']}\n"
            context += "\n"
        else:
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
- Use the EXACT VERBATIM lines as they appear in the transcript.
- DO NOT paraphrase, summarize, or modify the transcript text.
- Each point in your answer must consist of a verbatim line from the transcript followed by its timestamp in [start.0s - end.0s] format.
- If the answer is not present, say "Not mentioned in the video."
- Format as a list of bullet points.
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
