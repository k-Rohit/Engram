"""Golden-question eval — the definition of "good" for this brain.

Run after any change to ingestion, prompts, or models:

    python backend/eval/golden_eval.py

Hits the live API (start it first). A question passes if the answer contains
at least one expected keyword and isn't the empty-memory fallback. ~10 recall
calls => costs a few cents; that's the price of knowing recall still works.
"""

import sys
import time
import uuid

import requests

API = "http://localhost:8090"

# (question, [any of these keywords must appear in the answer, case-insensitive])
GOLDEN: list[tuple[str, list[str]]] = [
    ("What is the correct package name to install for the dotenv import error?",
     ["python-dotenv"]),
    ("How do LangGraph nodes update state?",
     ["partial", "reducer", "merge"]),
    ("What did I decide about which Docker services to run?",
     ["postgres", "airflow"]),
    ("What is a bool query in OpenSearch?",
     ["must", "should", "keyword", "opensearch", "clauses"]),
    ("What does the hybrid indexing service do?",
     ["embedding", "keyword", "semantic"]),
    ("What did I learn about chunking text for RAG?",
     ["chunk"]),
    ("How do I keep a knowledge graph consistent as it grows?",
     ["dedup", "entity resolution", "canonical", "duplicate"]),
    ("Why was git still tracking my venv folder after adding it to gitignore?",
     ["git rm", "cached", "already tracked", "already-tracked"]),
    ("What did I learn about namespace packages in Python?",
     ["__init__", "pep 420", "namespace"]),
    ("How does lru_cache maxsize work?",
     ["cache", "maxsize"]),
]


def run() -> int:
    print(f"Golden eval — {len(GOLDEN)} questions against {API}\n")
    passed = 0
    for i, (q, keywords) in enumerate(GOLDEN, 1):
        t0 = time.time()
        try:
            r = requests.post(
                f"{API}/ask",
                json={"question": q, "session_id": f"eval-{uuid.uuid4()}"},
                timeout=120,
            )
            answer = r.json().get("answer", "")
        except Exception as e:
            answer = f"<request failed: {e}>"
        secs = time.time() - t0

        low = answer.lower()
        empty = "nothing relevant" in low
        hit = next((k for k in keywords if k.lower() in low), None)
        ok = bool(hit) and not empty
        passed += ok

        mark = "PASS" if ok else "FAIL"
        why = f"matched {hit!r}" if ok else ("empty memory" if empty else f"none of {keywords}")
        print(f"  [{mark}] {i:02d} ({secs:4.0f}s) {q[:58]:58} — {why}")

    print(f"\n{passed}/{len(GOLDEN)} passed")
    return 0 if passed == len(GOLDEN) else 1


if __name__ == "__main__":
    sys.exit(run())
