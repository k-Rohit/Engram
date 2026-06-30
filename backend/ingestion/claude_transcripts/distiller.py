"""Step 2 — distill cleaned Claude conversations into atomic insight cards.

Run directly:  python backend/ingestion/claude_transcripts/distiller.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.config import DistillationLLMSettings
from backend.models.claude_transcripts.distillation import Card, Cards
from backend.ingestion.claude_transcripts.client import clean_all_sessions

load_dotenv()
_settings = DistillationLLMSettings()

DISTILL_PROMPT = """You are distilling a developer's past Claude Code conversation into atomic memory cards for their personal "second brain".

Extract EVERY distinct insight as a separate card. Capture three kinds:
- "concept": a conceptual question/doubt the user asked and its explanation (e.g. "what is a bool query?"). These are the MOST valuable — never skip them.
- "problem_solution": a concrete bug/error/issue and how it was fixed.
- "decision": a choice the user made and the reasoning behind it.

Rules:
- Preserve concrete specifics: exact errors, commands, file names, library/API names, code identifiers.
- Write answers addressing the user as "you".
- If the conversation contains no real insight, return an empty list.
- Never invent anything that isn't in the conversation.

Conversation:
"""


def build_distiller():
    """A LangChain runnable that returns a `Cards` object, with retry on rate limits."""
    llm = ChatOpenAI(
        model=_settings.dis_llm_model,
        base_url=_settings.base_url,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=_settings.temperature,
    )
    return llm.with_structured_output(Cards, method="json_schema").with_retry(
        stop_after_attempt=3
    )


def chunk_conversation(conversation: str, max_chars: int = 12000) -> list[str]:
    """Split a long conversation on turn boundaries so it fits the model context."""
    if len(conversation) <= max_chars:
        return [conversation]
    chunks: list[str] = []
    current = ""
    for turn in conversation.split("\n\n"):
        if current and len(current) + len(turn) + 2 > max_chars:
            chunks.append(current)
            current = ""
        current += turn + "\n\n"
    if current.strip():
        chunks.append(current)
    return chunks


def distill_conversation(conversation: str) -> list[Card]:
    """Turn one cleaned conversation into a list of insight cards."""
    distiller = build_distiller()
    cards: list[Card] = []
    for chunk in chunk_conversation(conversation):
        result: Cards = distiller.invoke(DISTILL_PROMPT + chunk)
        cards.extend(result.cards)
    return cards


if __name__ == "__main__":
    # Demo on ONE small session so we don't hammer the free model's rate limit.
    sessions = clean_all_sessions()
    demo = next(
        (s for s in sessions if 8 <= len(s["turns"]) <= 14),
        min(sessions, key=lambda s: len(s["turns"])),
    )
    print(f"Distilling: {demo['project']} ({len(demo['turns'])} turns)\n")

    cards = distill_conversation(demo["conversation"])
    print(f"Got {len(cards)} cards:\n")
    for c in cards:
        print(f"[{c.kind}] {c.title}")
        if c.question:
            print(f"   Q: {c.question}")
        print(f"   A: {c.answer[:200]}")
        print(f"   tags: {c.tags}\n")
