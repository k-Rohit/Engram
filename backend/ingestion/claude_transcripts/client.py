"""Step 1 — turn raw Claude Code transcripts into clean, ordered conversations.

Run directly:  python backend/ingestion/claude_transcripts/client.py
"""

import sys
import json
import re
from pathlib import Path

# Make the repo root importable when running this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Wrapper tags Claude injects that are noise for a second brain — strip the
# whole element (open tag, content, close tag).
_NOISE_TAGS = (
    "ide_opened_file", "ide_selection", "ide_diagnostics", "system-reminder",
    "command-name", "command-message", "local-command-caveat",
    "bash-input", "bash-stdout", "bash-stderr",
)
_NOISE_RE = re.compile(
    r"<(" + "|".join(_NOISE_TAGS) + r")>.*?</\1>",
    re.DOTALL,
)


def get_transcript_path() -> Path:
    """Where Claude stores session transcripts (one .jsonl per session)."""
    return Path.home() / ".claude" / "projects"


def list_sessions() -> list[Path]:
    """All session files, one level deep (skips memory/ and tool-results/)."""
    return sorted(get_transcript_path().glob("*/*.jsonl"))


def _clean(text: str) -> str:
    """Drop IDE/command wrapper tags and trim."""
    return _NOISE_RE.sub("", text).strip()


def extract_text(event: dict) -> str:
    """Pull human-readable text from a user/assistant event.

    Handles both content shapes: a plain string, or a list of blocks (we keep
    only `text` blocks — `thinking`, `tool_use`, `tool_result` are dropped).
    """
    content = event.get("message", {}).get("content")
    if isinstance(content, str):
        return _clean(content)
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if b.get("type") == "text"]
        return _clean("\n".join(p for p in parts if p))
    return ""


def project_label(session_path: Path) -> str:
    """Real project name, read from the `cwd` field inside the session."""
    for line in session_path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            cwd = json.loads(line).get("cwd")
        except json.JSONDecodeError:
            continue
        if cwd:
            return Path(cwd).name
    return session_path.parent.name


def clean_session(session_path: Path) -> dict:
    """Parse one session into ordered, fluff-free turns + a formatted conversation."""
    turns: list[dict] = []
    session_id: str | None = None

    for line in session_path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") not in ("user", "assistant"):
            continue
        if event.get("isMeta"):
            continue

        text = extract_text(event)
        if not text:                       # tool_result / thinking-only lines
            continue

        session_id = session_id or event.get("sessionId")
        turns.append({"role": event["message"]["role"], "text": text})

    conversation = "\n\n".join(f"{t['role'].title()}: {t['text']}" for t in turns)
    return {
        "project": project_label(session_path),
        "session_id": session_id or session_path.stem,
        "source": "claude_code",
        "turns": turns,
        "conversation": conversation,
    }


def clean_all_sessions() -> list[dict]:
    """Clean every session that has real conversation in it."""
    out = []
    for path in list_sessions():
        cleaned = clean_session(path)
        if cleaned["turns"]:
            out.append(cleaned)
    return out


if __name__ == "__main__":
    sessions = clean_all_sessions()
    print(f"Cleaned {len(sessions)} sessions\n")
    for s in sessions:
        print(f"  {s['project']:24} {len(s['turns']):4} turns  ({s['session_id'][:8]})")

    # Show a sample so you can eyeball the quality
    if sessions:
        sample = min(sessions, key=lambda s: len(s["turns"]))
        print("\n--- sample cleaned conversation:", sample["project"], "---")
        print(sample["conversation"][:900])
