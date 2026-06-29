"""Pydantic request/response schemas for the FastAPI endpoints."""

from pydantic import BaseModel


class IngestClaudeCodeRequest(BaseModel):
    # Encoded project-dir name under ~/.claude/projects (the `id` from /claude/projects).
    source_project: str


class IngestArticleRequest(BaseModel):
    project: str
    url: str
    # Paste fallback: used when trafilatura can't extract the URL (paywalled/blocked).
    content: str | None = None


class AskRequest(BaseModel):
    project: str
    question: str


class Source(BaseModel):
    source: str            # claude_code | article | ...
    label: str | None = None
    date: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Source] = []


class GraphNode(BaseModel):
    id: str
    label: str
    source: str | None = None


class GraphEdge(BaseModel):
    source: str            # node id
    target: str            # node id
    label: str | None = None


class GraphResponse(BaseModel):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
