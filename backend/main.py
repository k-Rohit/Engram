"""Engram FastAPI app — all endpoints.

Run:  PYTHONPATH=. uv run uvicorn backend.main:app --reload --port 8090
(8090 to avoid Cognee's own UI backend on :8000.)

All Cognee access goes through backend.memory.cognee_client — never call
cognee directly from an endpoint.
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.config import configure_cognee
from backend.ingestion import claude_code as cc
from backend.memory import cognee_client
from backend.models import (
    AskRequest,
    AskResponse,
    IngestClaudeCodeRequest,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Engram")

# TanStack/Vite dev origins. This scaffold (Lovable) defaults to :8080, and
# falls back to :8081 if 8080 is taken.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", "http://localhost:8081",
        "http://localhost:3000", "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    configure_cognee()


@app.get("/claude/projects")
async def claude_projects():
    """List Claude Code projects with sessions/lines and whether each is ingested."""
    ingested = set(await cognee_client.list_dataset_names())
    projects = cc.list_project_meta()
    for p in projects:
        p["ingested"] = p["dataset"] in ingested
    return projects


@app.post("/ingest/claude-code")
async def ingest_claude_code(req: IngestClaudeCodeRequest):
    """Ingest all sessions of one Claude project into its own dataset."""
    encoded = req.source_project
    if not encoded:
        raise HTTPException(400, "source_project (encoded project dir) is required")

    # Cap turns/session so a huge project stays bounded in time/cost. Raise later.
    docs = cc.parse_transcripts(source_project=encoded, max_turns_per_session=40)
    if not docs:
        raise HTTPException(404, f"No transcripts found for {encoded}")

    dataset = cc.dataset_name(encoded)
    label = cc.project_label(encoded)
    for d in docs:
        await cognee_client.ingest(
            d["text"], dataset=dataset, source="claude_code",
            metadata={"Project": label, "Session": d["session"]},
        )
        logger.info("ingested session %s into %s", d["session"], dataset)

    return {"dataset": dataset, "project": label, "documents": len(docs)}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """Recall a cited answer from a project's dataset."""
    answer, _ = await cognee_client.query(req.question, dataset=req.project)
    return AskResponse(answer=answer or "Nothing relevant found in memory.")


@app.get("/projects")
async def projects():
    """List all Engram datasets (ingested projects)."""
    return await cognee_client.list_dataset_names()
