import json, subprocess, sys

MODEL = "llama3"
QUESTION = "What is a balance sheet?"

def ollama_run(model: str, prompt: str) -> str:
    # Stream JSON from `ollama run --json`
    p = subprocess.Popen(["ollama", "run", model, "--json"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert p.stdin is not None
    p.stdin.write(prompt.encode()); p.stdin.close()

    out = ""
    for line in p.stdout:  # type: ignore
        try:
            j = json.loads(line.decode("utf-8", errors="ignore"))
            out += j.get("response", "")
        except Exception:
            continue
    rc = p.wait()
    if rc != 0:
        err = p.stderr.read().decode()
        raise RuntimeError(f"ollama run failed (rc={rc}): {err}")
    return out.strip()

if __name__ == "__main__":
    try:
        print(f"🔎 Testing Ollama model: {MODEL}")
        ans = ollama_run(MODEL, QUESTION)
        print("\n✅ Response:")
        print(ans[:800] + ("..." if len(ans) > 800 else ""))
    except Exception as e:
        print("\n❌ Failed:", e)
        print("\nTroubleshoot:")
        print("1) Is Ollama running?   curl http://127.0.0.1:11434/api/tags")
        print("2) Pull model:           ollama pull llama3")
        print("3) Test CLI:             ollama run llama3 \"Hello\"")
        sys.exit(1)
