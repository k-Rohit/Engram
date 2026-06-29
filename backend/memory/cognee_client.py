"""All Cognee access goes through here — endpoints never call cognee directly.

Cognee 1.2.2 API cheatsheet:
- remember(data, dataset_name=...)      ingest + build knowledge graph (one call)
- recall(query_text, datasets=[...])    natural-language Q&A, auto-routed retrieval
- forget(dataset=... / everything=True) delete memory
- datasets.list_datasets()              async; returns Dataset objs (.name/.id)
- recall() returns typed Pydantic entries (ResponseGraphEntry, QAEntry, ...),
  NOT strings. Read the answer off the entry's `.text`.
"""

import logging

import cognee

logger = logging.getLogger(__name__)


async def ingest(content: str, dataset: str, source: str, metadata: dict | None = None) -> None:
    """Tag content with provenance and remember() it into a dataset.

    The [Source]/[Project] prefix is how provenance survives into the graph so
    recall() can cite it later.
    """
    tag = f"[Source: {source}]"
    for k, v in (metadata or {}).items():
        tag += f" [{k}: {v}]"
    tagged = f"{tag}\n\n{content}"
    await cognee.remember(tagged, dataset_name=dataset)


async def query(question: str, dataset: str):
    """Recall a cited answer from one dataset. Returns (answer_text, raw_results)."""
    results = await cognee.recall(
        question,
        datasets=[dataset],
        context_profile="qa",
        include_references=True,
    )
    answer = "\n\n".join(getattr(r, "text", "") for r in results if getattr(r, "text", ""))
    return answer, results


async def list_dataset_names() -> list[str]:
    """Names of datasets that currently exist in Cognee (== ingested projects)."""
    datasets = await cognee.datasets.list_datasets()
    return [d.name for d in (datasets or [])]


async def graph(dataset: str):
    """Return nodes + edges for a dataset's knowledge graph.

    NOTE: cognee.get_graph_data() does NOT exist in 1.2.2. Options:
      - cognee.visualize_graph(destination_file_path=...)  -> HTML
      - cognee.get_memory_provenance_graph(...)            -> provenance chain
      - cognee.low_level / graph engine                    -> raw nodes+edges JSON
    """
    raise NotImplementedError
