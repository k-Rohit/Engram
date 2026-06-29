"""Quick Cognee smoke test — verifies your key + the remember/recall round-trip.

Run:  uv run python scripts/test_cognee.py

Prints the TYPE of each recall result so you can see the real shape you'll
parse in cognee_client.query().
"""

import asyncio

from backend.config import configure_cognee


async def main() -> None:
    configure_cognee()
    import cognee

    await cognee.forget(everything=True)  # clean slate
    await cognee.remember(
        "[Source: claude_code] [Project: engram] "
        "We fixed a CORS error by adding FastAPI CORSMiddleware with "
        "allow_origins=['http://localhost:5173'].",
        dataset_name="engram",
    )

    results = await cognee.recall(
        "How did I fix CORS before?",
        datasets=["engram"],
        context_profile="qa",
        include_references=True,
    )
    for r in results:
        print(type(r).__name__, "->", getattr(r, "text", r))


if __name__ == "__main__":
    asyncio.run(main())
