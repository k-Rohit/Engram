import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
class NotionClient:
    """Reads a Notion workspace into plain-text documents. Get the singleton
    instance from factory.get_client()."""

    def __init__(self) -> None:
        self.client = Client(auth=os.getenv("NOTION_API_KEY"))

    def _get_block_text(self, block: dict) -> str:
        """Extract plain text from a single block's rich_text (empty if none)."""
        block_type = block.get("type")
        value = block.get(block_type, {})
        rich_text = value.get("rich_text", [])
        return "".join(t.get("plain_text", "") for t in rich_text)

    def read_blocks(self, block_id: str) -> list[str]:
        """Recursively read all text blocks under a block/page, with pagination."""
        texts: list[str] = []
        cursor = None
        while True:
            kwargs = {"block_id": block_id}
            if cursor:
                kwargs["start_cursor"] = cursor
            response = self.client.blocks.children.list(**kwargs)
            for block in response["results"]:
                text = self._get_block_text(block)
                if text:
                    texts.append(text)
                if block.get("has_children"):
                    texts.extend(self.read_blocks(block["id"]))  # recurse into children

            if response.get("has_more"):
                cursor = response["next_cursor"]
            else:
                break
        return texts

    def get_page_title(self, page: dict) -> str:
        """Pull the title text off a page's properties."""
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "title":
                title = "".join(x.get("plain_text", "") for x in prop["title"])
                return title or "Untitled"
        return "Untitled"

    def get_all_pages(self) -> list[dict]:
        """Search the workspace for every page, following pagination."""
        pages: list[dict] = []
        cursor = None
        while True:
            kwargs = {"filter": {"property": "object", "value": "page"}}
            if cursor:
                kwargs["start_cursor"] = cursor
            response = self.client.search(**kwargs)

            pages.extend(response["results"])
            if response.get("has_more"):
                cursor = response["next_cursor"]
            else:
                break
        return pages

    def extract_workspace(self) -> list[dict]:
        """Return every page as {page_id, title, content}."""
        pages = self.get_all_pages()
        documents: list[dict] = []
        print(f"Found {len(pages)} pages\n")
        for page in pages:
            page_id = page["id"]
            title = self.get_page_title(page)
            print(f"Reading: {title}")
            content = "\n".join(self.read_blocks(page_id))
            documents.append({
                "page_id": page_id,
                "title": title,
                "content": content,
                "last_edited": page.get("last_edited_time", ""),
            })
        return documents


if __name__ == "__main__":
    from backend.ingestion.notion.factory import get_client

    docs = get_client().extract_workspace()
    print("\n--------------------------------------")
    for doc in docs:
        print(f"\nTITLE : {doc['title']}")
        print("=" * 50)
        print(doc["content"][:500])
