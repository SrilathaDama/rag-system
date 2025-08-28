# app/llm/generate.py
import requests, json

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
SYSTEM = "Answer the question using the provided context. Use the information from the context to give a helpful and complete answer. If the context contains relevant information, use it to explain the concept. Only say 'I don't know' if the context contains no relevant information at all."

def build_prompt(question: str, contexts: list[str]) -> str:
    context_block = "\n\n---\n\n".join(contexts)
    return f"{SYSTEM}\n\nContext:\n{context_block}\n\nQuestion:\n{question}\n\nAnswer concisely."

def ollama_generate(model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=300)
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception as e:
        return f"Error: {e}"
