import json

def build_prompt(query, retrieved_chunks, n_answers=3):
    """Constructs the augmented prompt for the LLM with multi-answer support."""
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
- Identify up to {n_answers} distinct, relevant answers from the transcript.
- Each answer should cover a DIFFERENT part of the transcript (non-overlapping).
- Return your response as a valid JSON array with this structure:
[
  {{
    "answer": "concise answer text",
    "start_time": <start timestamp in seconds>,
    "end_time": <end timestamp in seconds>,
    "relevance": "brief explanation of why this is relevant"
  }}
]
- Rank answers by relevance (most relevant first).
- If fewer than {n_answers} distinct answers exist, return only what's relevant.
- If no answer is found, return: [{{"answer": "Not mentioned in the video.", "start_time": null, "end_time": null, "relevance": "N/A"}}]
- Return ONLY the JSON array, no other text.
"""

def parse_llm_response(response_text):
    """Parses the structured JSON response from the LLM."""
    try:
        # Strip markdown code fences if present
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]  # Remove first line (```json)
            text = text.rsplit("```", 1)[0]  # Remove last ``` 
        return json.loads(text.strip())
    except json.JSONDecodeError:
        # Fallback: return as single unstructured answer
        return [{"answer": response_text, "start_time": None, "end_time": None, "relevance": "Raw response (parsing failed)"}]

def ask_llm(prompt, client, model="gpt-4o-mini"):
    """Sends prompt to OpenAI Chat API."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON when asked to."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
