import sys
from pathlib import Path

# Make the repo root importable so `backend...` works when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.memory.cognee_client import ask, sync
from backend.ingestion.claude_transcripts.pipeline import run as distill_claude

app = FastAPI(title="Engram")

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


class AskRequest(BaseModel):
    question: str
    session_id: str | None = None


@app.post("/ask")
async def ask_endpoint(req: AskRequest):
    """Query the whole second brain; returns {answer, sources}."""
    return await ask(req.question, session_id=req.session_id)


@app.post("/sync/claude")
async def sync_claude():
    """Distill any new Claude turns into cards, then add new cards to the graph."""
    await asyncio.to_thread(distill_claude)  # clean -> distill -> Supabase (new turns only)
    return await sync("claude")              # new cards -> Cognee


@app.post("/sync/notion")
async def sync_notion():
    """Fetch Notion pages; add any new ones to the graph."""
    return await sync("notion")


@app.post("/sync/gmail")
async def sync_gmail():
    """Fetch newsletters; add any new ones to the graph."""
    return await sync("gmail")


if __name__ == "__main__":
    # Cognee's graph DB is single-process — don't run an ingest or the Cognee UI
    # while this is up.
    uvicorn.run(app, host="127.0.0.1", port=8090, log_level="info")
