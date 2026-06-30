"""Pydantic models for the distilled output of a Claude Code conversation."""

from typing import Literal

from pydantic import BaseModel, Field


class Card(BaseModel):
    """One atomic insight distilled from a conversation."""

    kind: Literal["concept", "problem_solution", "decision"] = Field(
        description=(
            "concept = a conceptual question/doubt the user asked + its explanation; "
            "problem_solution = a concrete bug/error and how it was fixed; "
            "decision = a choice the user made and the reasoning"
        )
    )
    title: str = Field(description="short headline of the insight")
    question: str = Field(
        default="", description="what the user asked (for concept / decision cards)"
    )
    answer: str = Field(
        description="the explanation, fix, or rationale — keep concrete specifics "
        "(exact errors, commands, file/library names)"
    )
    tags: list[str] = Field(default_factory=list)


class Cards(BaseModel):
    """Wrapper so structured output can return a list of cards."""

    cards: list[Card] = Field(default_factory=list)
