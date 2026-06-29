"""Parse Claude Code transcripts into ingestible documents.

Real location on this machine (NOT /mnt/transcripts as CLAUDE.md says):
    ~/.claude/projects/<encoded-project-dir>/<session-uuid>.jsonl

Each .jsonl is one session, one JSON object per line. Lines have a `type`
field; the conversational ones are `type in {"user", "assistant"}` (others:
ai-title, last-prompt, queue-operation, attachment, mode,
file-history-snapshot, system — skipped).

Message shape:
    user      -> message.content is usually a str (sometimes a list of
                 tool_result blocks, which we skip).
    assistant -> message.content is a list of blocks; we keep the `text`
                 blocks and skip `thinking` / `tool_use`.

`parse_transcripts()` returns one document per session: the turns concatenated
into a readable transcript, plus metadata (session id, project dir, start time).
"""

import json
import pathlib
import re

TRANSCRIPTS_ROOT = pathlib.Path.home() / ".claude" / "projects"

# User turns that are tool/command plumbing, not real conversation.
_NOISE_USER_PREFIXES = (
    "<local-command-caveat>",
    "<command-name>",
    "<command-message>",
    "<bash-input>",
    "<bash-stdout>",
    "<bash-stderr>",
    "Caveat:",
)


def decode_project_name(encoded: str) -> str:
    """`-Users-kumarrohit-Desktop-Langgraph` -> `/Users/kumarrohit/Desktop/Langgraph`."""
    return encoded.replace("-", "/")


def list_projects() -> list[str]:
    """Return the encoded project-dir names under ~/.claude/projects (non-empty only)."""
    if not TRANSCRIPTS_ROOT.exists():
        return []
    out = []
    for p in TRANSCRIPTS_ROOT.iterdir():
        if p.is_dir() and any(p.glob("*.jsonl")):
            out.append(p.name)
    return out


def dataset_name(encoded: str) -> str:
    """Stable, Cognee-safe dataset name for a project dir (lossless + unique)."""
    return "cc_" + re.sub(r"[^a-z0-9]+", "_", encoded.lower()).strip("_")


def project_label(encoded: str) -> str:
    """Human label for a project, read from the real `cwd` in its transcript.

    Falls back to the (lossy) decoded folder name if cwd can't be read.
    """
    d = TRANSCRIPTS_ROOT / encoded
    for jsonl in sorted(d.glob("*.jsonl")):
        for line in jsonl.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            cwd = row.get("cwd")
            if cwd:
                return pathlib.Path(cwd).name
        break
    return decode_project_name(encoded)


def list_project_meta() -> list[dict]:
    """Metadata for every non-empty Claude project, for the frontend list.

    Returns: [{id, name, dataset, sessions, lines}]  (id = encoded dir name).
    """
    out = []
    for encoded in list_projects():
        d = TRANSCRIPTS_ROOT / encoded
        files = list(d.glob("*.jsonl"))
        lines = sum(sum(1 for _ in f.open(encoding="utf-8")) for f in files)
        out.append({
            "id": encoded,
            "name": project_label(encoded),
            "dataset": dataset_name(encoded),
            "sessions": len(files),
            "lines": lines,
        })
    return sorted(out, key=lambda m: m["lines"], reverse=True)


def _extract_text(message: dict) -> str:
    """Pull human-readable text out of a user/assistant message."""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")).strip())
        return "\n".join(p for p in parts if p)
    return ""


def _is_noise_user(text: str) -> bool:
    return text.startswith(_NOISE_USER_PREFIXES)


def _parse_session_file(path: pathlib.Path, max_turns: int | None = None) -> dict | None:
    """Turn one .jsonl session file into a single document dict, or None if empty."""
    turns: list[str] = []
    session_id: str | None = None
    started_at: str | None = None

    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue

        if row.get("type") not in ("user", "assistant"):
            continue
        if row.get("isMeta"):
            continue

        message = row.get("message")
        if not isinstance(message, dict):
            continue

        text = _extract_text(message)
        if not text:
            continue

        role = message.get("role", row.get("type"))
        if role == "user" and _is_noise_user(text):
            continue

        session_id = session_id or row.get("sessionId")
        started_at = started_at or row.get("timestamp")

        label = "User" if role == "user" else "Assistant"
        turns.append(f"{label}: {text}")

        if max_turns is not None and len(turns) >= max_turns:
            break

    if not turns:
        return None

    return {
        "session": session_id or path.stem,
        "project_dir": path.parent.name,
        "started_at": started_at,
        "text": "\n\n".join(turns),
    }


def parse_transcripts(
    source_project: str | None = None,
    max_sessions: int | None = None,
    max_turns_per_session: int | None = None,
) -> list[dict]:
    """Walk transcripts and return one document per session.

    Args:
        source_project: encoded project-dir name (e.g. "-Users-kumarrohit-Desktop-Langgraph").
                        None = every project.
        max_sessions: cap total sessions returned (useful to keep ingest cheap/fast).
        max_turns_per_session: cap turns per session document.

    Returns:
        [{"session", "project_dir", "started_at", "text"}, ...]
    """
    if not TRANSCRIPTS_ROOT.exists():
        return []

    if source_project:
        dirs = [TRANSCRIPTS_ROOT / source_project]
    else:
        dirs = [p for p in TRANSCRIPTS_ROOT.iterdir() if p.is_dir()]

    docs: list[dict] = []
    for d in dirs:
        if not d.exists():
            continue
        for jsonl in sorted(d.glob("*.jsonl")):
            doc = _parse_session_file(jsonl, max_turns=max_turns_per_session)
            if doc:
                docs.append(doc)
            if max_sessions is not None and len(docs) >= max_sessions:
                return docs
    return docs
