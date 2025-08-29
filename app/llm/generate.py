# app/llm/generate.py
import requests, json

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
SYSTEM = "You are a helpful assistant. Answer questions using ONLY the provided context. If the context contains information that directly answers the question, provide a complete answer. If the context does not contain relevant information to answer the question, respond with 'I don't know.' Do not use any knowledge outside the provided context."

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
