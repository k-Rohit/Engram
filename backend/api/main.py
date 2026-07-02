import sys
from pathlib import Path

# Make the repo root importable so `backend...` works when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import os
import asyncio

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.memory.cognee_client import (
    ask,
    capture_note,
    consolidate_feedback,
    record_feedback,
    stats,
    sync,
)
from backend.ingestion.claude_transcripts.pipeline import run as distill_claude

app = FastAPI(title="Engram")

# One writer at a time: Cognee's stores are single-process, and concurrent
# ingests would double-insert (no dedup). 409 if a sync is already running.
_write_lock = asyncio.Lock()

# Frontend dev origins (TanStack/Vite land on 8080/8081).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", "http://localhost:8081",
        "http://localhost:3000", "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello!"}


@app.get("/health")
def check_health():
    return {"status": "Healthy"}


@app.get("/stats")
def get_stats():
    """Live doc counts per source, from the durable graph ledger."""
    return stats()


class AskRequest(BaseModel):
    question: str
    session_id: str | None = None


@app.post("/ask")
async def ask_endpoint(req: AskRequest):
    """Query the whole second brain; returns {answer, sources}."""
    return await ask(req.question, session_id=req.session_id)


class CaptureRequest(BaseModel):
    text: str


@app.post("/capture")
async def capture_endpoint(req: CaptureRequest):
    """Quick capture — 'remember this' straight into the graph."""
    if not req.text.strip():
        raise HTTPException(400, "empty note")
    async with _write_lock:
        return await capture_note(req.text)


class FeedbackRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    score: int  # +1 / -1
    text: str = ""


@app.post("/feedback")
async def feedback_endpoint(req: FeedbackRequest):
    """Rate an answer; feeds recall ranking now, improve() on consolidation."""
    return await record_feedback(req.session_id, req.question, req.answer, req.score, req.text)


@app.post("/improve")
async def improve_endpoint():
    """Bridge all pending feedback into the permanent graph (costs LLM calls)."""
    if _write_lock.locked():
        raise HTTPException(409, "a sync is already running — try again shortly")
    async with _write_lock:
        return await consolidate_feedback()


async def _run_sync(source: str):
    if _write_lock.locked():
        raise HTTPException(409, "a sync is already running — try again shortly")
    async with _write_lock:
        if source == "claude":
            await asyncio.to_thread(distill_claude)  # new turns -> cards (Supabase)
        return await sync(source)


@app.post("/sync/claude")
async def sync_claude():
    return await _run_sync("claude")


@app.post("/sync/notion")
async def sync_notion():
    return await _run_sync("notion")


@app.post("/sync/gmail")
async def sync_gmail():
    return await _run_sync("gmail")


# ---------- auto-sync: the brain captures without being asked ----------

AUTO_SYNC_MINUTES = int(os.getenv("AUTO_SYNC_MINUTES", "60"))


async def _auto_sync_loop():
    while True:
        await asyncio.sleep(AUTO_SYNC_MINUTES * 60)
        try:
            if _write_lock.locked():
                continue  # a manual sync is running; catch it next cycle
            async with _write_lock:
                await asyncio.to_thread(distill_claude)
                result = await sync()  # all sources, incremental
            print(f"[auto-sync] {result}")
        except Exception as e:  # never let the loop die
            print(f"[auto-sync] failed: {type(e).__name__}: {e}")


@app.on_event("startup")
async def _start_auto_sync():
    asyncio.create_task(_auto_sync_loop())


if __name__ == "__main__":
    # Cognee's graph DB is single-process — don't run ingest scripts or the
    # Cognee UI while this is up.
    uvicorn.run(app, host="127.0.0.1", port=8090, log_level="info")
