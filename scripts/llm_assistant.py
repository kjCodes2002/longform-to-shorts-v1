def build_prompt(query, retrieved_chunks):
    """Constructs the augmented prompt for the LLM."""
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

def ask_llm(prompt, client, model="gpt-4o-mini"):
    """Sends prompt to OpenAI Chat API."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
