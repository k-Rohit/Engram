# Engram — Project Context for Claude Code

## What This Project Is

Engram is a personal second brain for knowledge workers who use AI tools heavily (Claude Code, ChatGPT, Notion, Google Drive). It ingests conversations and notes from these sources, builds a persistent knowledge graph using Cognee, and lets users query their own learning history across sessions.

**The core pain it solves:** You ask Claude a great question, get a great answer, and forget it two weeks later. You ask the same question again. Engram ends that cycle — everything you've learned, decided, or debugged is queryable forever.

**One-line pitch:** "Every answer you've gotten from Claude Code lives in your second brain. Ask it anything — it remembers what you forgot."

---

## Tech Stack

| Layer | Tool |
|---|---|
| Package manager | uv |
| Memory engine | Cognee |
| Agent orchestration | LangGraph |
| Backend | FastAPI |
| Frontend | React + Cytoscape.js |
| LLM | Claude via Anthropic API (claude-sonnet-4-6) |
| Input 1 | Claude Code transcripts (`/mnt/transcripts`) |
| Input 2 | Google Drive via MCP (`https://drivemcp.googleapis.com/mcp/v1`) |
| Input 3 | ChatGPT JSON export (conversation picker UI) |
| Input 4 | Web article / Medium / blog URL (trafilatura fetch + parse) |
| Input 5 | Medium article paste fallback (for paywalled content) |

---

## Project Structure

```
engram/
├── pyproject.toml
├── CLAUDE.md                  # This file
├── .env                       # API keys (never commit)
├── backend/
│   ├── main.py                # FastAPI app + all endpoints
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── claude_code.py     # Parse /mnt/transcripts JSON files
│   │   ├── chatgpt.py         # Parse ChatGPT export conversations.json
│   │   ├── gdrive.py          # Fetch docs via Google Drive MCP
│   │   └── article.py         # Fetch + parse web article from URL
│   ├── memory/
│   │   ├── __init__.py
│   │   └── cognee_client.py   # All cognee.add / cognify / search logic
│   └── agent/
│       ├── __init__.py
│       └── query_agent.py     # LangGraph agent for querying memory
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.jsx            # Two-panel layout
│       ├── ChatPanel.jsx      # Chat interface
│       └── GraphPanel.jsx     # Cytoscape.js knowledge graph
└── scripts/
    └── test_cognee.py         # Quick smoke test for Cognee setup
```

---

## Environment Variables

```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=        # Cognee uses OpenAI by default for embeddings
COGNEE_DB_PATH=./cognee_db
```

---

## Core Data Flow

```
Source (Claude Code / ChatGPT / Drive / Article)
    ↓
Ingestion layer (parse + clean + tag with project + source)
    ↓
cognee.add(content, dataset_name=project)
    ↓
cognee.cognify(dataset_name=project)   ← builds knowledge graph
    ↓
cognee.search(query, dataset_name=project)   ← query time
    ↓
LangGraph synthesizer node   ← generates cited answer
    ↓
FastAPI response → React frontend
```

---

## Ingestion Details

### Claude Code Transcripts
- Location: `/mnt/transcripts/`
- Format: JSON files, one per conversation
- Key fields to extract: `messages[].role`, `messages[].content`, `created_at`, title if available
- Tag every ingested piece with `[Source: claude_code] [Project: <project_name>]`

### ChatGPT Export
- User exports from ChatGPT Settings → Data Export → `conversations.json`
- Format: array of conversations with `title`, `create_time`, `messages[]`
- Show user a checklist of conversation titles — only ingest selected ones
- Tag with `[Source: chatgpt]`

### Google Drive MCP
- MCP server URL: `https://drivemcp.googleapis.com/mcp/v1`
- User specifies a folder name or document name
- Make Anthropic API call with `mcp_servers` param to fetch content
- Tag with `[Source: google_drive]`

### Web Article (Medium, blogs, any public page)
- User pastes a URL
- Use `trafilatura` as the primary extractor — it handles Medium, Substack, dev.to, and most blogs cleanly
- If `trafilatura.fetch_url(url)` returns `None` (paywalled or blocked), show a paste fallback UI: "Couldn't extract article — paste content here"
- Never use httpx + BeautifulSoup as primary — trafilatura is strictly better for article extraction
- Tag with `[Source: article] [URL: <url>]`

```python
import trafilatura

def fetch_article(url: str) -> str | None:
    content = trafilatura.fetch_url(url)
    return content  # None if paywalled or failed
```

---

## Cognee Client (memory/cognee_client.py)

```python
import cognee

async def ingest(content: str, project: str, source: str, metadata: dict = {}):
    tag = f"[Project: {project}] [Source: {source}]"
    for k, v in metadata.items():
        tag += f" [{k}: {v}]"
    tagged = f"{tag}\n\n{content}"
    await cognee.add(tagged, dataset_name=project)
    await cognee.cognify(dataset_name=project)

async def query(question: str, project: str) -> str:
    results = await cognee.search(question, dataset_name=project)
    return str(results)

async def get_graph(project: str):
    return await cognee.get_graph_data(project)
```

---

## LangGraph Query Agent (agent/query_agent.py)

Two nodes only — keep it simple:

1. **MemorySearchNode** — calls `cognee.search()` with the user's question
2. **SynthesizerNode** — takes memory results, calls Claude to produce a cited, natural language answer

The synthesizer prompt must:
- Answer only from what's in memory (no hallucination)
- Cite the source (claude_code / chatgpt / google_drive / article) for each insight
- Include approximate date if available
- If nothing relevant found, say so honestly — do not make things up

---

## FastAPI Endpoints (backend/main.py)

```
POST /ingest/claude-code        # body: { project: str }  — reads all /mnt/transcripts
POST /ingest/chatgpt            # body: { project: str, selected_titles: list[str] }, file upload
POST /ingest/gdrive             # body: { project: str, folder_or_doc: str }
POST /ingest/article            # body: { project: str, url: str, content: str | None } — content used when URL extraction fails (paste fallback)
POST /ask                       # body: { project: str, question: str }
GET  /graph/{project}           # returns nodes + edges for Cytoscape.js
GET  /projects                  # list all dataset names in Cognee
```

CORS must be enabled for localhost:5173 (Vite dev server).

---

## Frontend (React)

Two-panel layout, full viewport height:
- **Left panel (60%):** Chat interface. Messages alternate user/brain. Input box at bottom.
- **Right panel (40%):** Cytoscape.js knowledge graph. Nodes colored by source:
  - Purple → claude_code
  - Blue → chatgpt
  - Green → google_drive
  - Amber → article

On every `/ask` response, refresh the graph via `/graph/{project}`.

Show a project selector dropdown at the top.

Show ingestion buttons: "Sync Claude Code", "Upload ChatGPT Export", "Sync Drive Folder", "Add Article / Medium URL".

---

## Coding Rules

- Fix only what is asked — do not refactor unrelated code
- Do not change variable names or function signatures unless asked
- Do not add helper functions that weren't requested
- Keep functions small and single-purpose
- Async everywhere in the backend (FastAPI + Cognee are both async)
- No print statements in production code — use Python logging
- All Cognee calls go through `memory/cognee_client.py` — never call cognee directly from endpoints
- Type hints on all function signatures

---

## What NOT to Build (out of scope for hackathon)

- User authentication / multi-user support
- Database other than Cognee's built-in storage
- Voice input
- Mobile responsive design
- Deployment / Docker / cloud hosting
- Browser extension

---

## Demo Script (Day 6 goal)

Three queries that must work flawlessly:

1. **Cross-session recall:** "Have I solved a CORS issue before and how did I fix it?"
   - Should cite a specific Claude Code conversation

2. **Concept connection:** "What do I know about Cognee's cognify performance?"
   - Should synthesize across multiple sources if available

3. **Decision retrieval:** "Why did I choose LangGraph over other orchestration frameworks?"
   - Should recall the reasoning from a past conversation

If all three work cleanly, the demo is ready.

---

## Hackathon Submission Framing

**Problem:** Knowledge workers using AI tools daily lose their best insights across fragmented sessions. They re-ask the same questions weeks later.

**Solution:** Engram ingests your AI conversations and notes into a Cognee knowledge graph — so your second brain grows every time you learn something new.

**Why Cognee specifically:** RAG retrieves chunks. Cognee builds a graph of how concepts connect across sources and time. When you ask "why did I make this decision?", Cognee traces the reasoning chain — not just the nearest embedding.

**Why not just RAG:** A vector DB stores what you put in. Cognee's `cognify()` infers relationships you didn't think to store — connecting a debugging session to a concept to a decision made three weeks later.