# llm/generator.py
from openai import OpenAI
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """You are ICMAB's official AI assistant. 
Answer questions using ONLY the provided context.
If the answer is not in the context, say: 
"I don't have that information. Please contact ICMAB directly."
Be concise, accurate, and professional.
Never make up information."""

def generate(query: str, chunks: list[dict]) -> dict:
    context = "\n\n".join([
        f"[{c['category'].upper()}] {c['text']}"
        for c in chunks
    ])
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": 
             f"Context:\n{context}\n\nQuestion: {query}"}
        ],
        temperature=0.1,     # low temp = factual, consistent
        max_tokens=512
    )
    
    return {
        "answer": response.choices[0].message.content,
        "sources": [
            {"title": c["title"], "category": c["category"],
             "url": c.get("url")}
            for c in chunks
        ]
    }