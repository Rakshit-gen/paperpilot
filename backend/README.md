# paperpilot backend

FastAPI service that does the actual work: ingest PDFs, answer questions
with citations, summarize a paper, and generate flashcards. See the root
`README.md` for the overall pitch.

## Setup

Needs Python 3.11 (a `.python-version` file pins this).

```
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # then add your GROQ_API_KEY
```

Run it:

```
uvicorn paperpilot.api:app --reload
```

Run the tests:

```
pytest tests/ -q
```

## API

- `GET /health`
- `GET /papers` — list ingested papers
- `POST /papers/upload` — multipart upload, `.pdf` only, 25mb max
- `POST /ask` — `{"question": "...", "paper_id": "optional, scopes to one paper"}`
- `POST /papers/{paper_id}/summarize`
- `POST /papers/{paper_id}/flashcards?count=5`

## Why Groq calls are wrapped in retries

Groq is fast but it's still a network call, and a single dropped
connection shouldn't fail someone's question. `llm.py` wraps every
chain invocation in three attempts with exponential backoff before
giving up and surfacing a real error.

## Production considerations

This is a real, working backend, not a demo, but a few things are
simplified on purpose for a project this size:

- **A single local Chroma store.** `CHROMA_DIR` is a directory on one
  machine. Running more than one backend instance, or wanting the paper
  library to survive a container being replaced, needs a shared vector
  store (a hosted Chroma, Qdrant, or pgvector instance) instead of local
  disk.
- **No auth.** Anyone who can reach the API can upload papers and ask
  questions. A real deployment needs this behind at least an API key,
  since it's happy to run up Groq usage for whoever can reach it.
- **No rate limiting.** Nothing stops repeated uploads or questions from
  hammering Groq. Worth adding before this is open to more than a
  trusted circle.
- **Secrets from a `.env` file.** Fine for local dev, but production
  wants a real secrets manager instead of an env var on a host.
- **Uploaded PDFs are kept as temp files under `UPLOAD_DIR`.** They're
  never cleaned up. For real usage you'd want either a retention policy
  or to drop the original file entirely once it's chunked and embedded,
  since the vector store is what actually answers questions.
- **Observability.** Structured logging is in place, but there's no
  tracing or metrics: no visibility into Groq latency, retry counts, or
  how often the corrective RAG path decides context is insufficient.

## Layout

```
src/paperpilot/
  config.py       env vars and constants
  store.py        chroma wrapper, plus per-paper chunk lookup
  registry.py     json sidecar of paper metadata (title, filename, page count)
  pdf_ingest.py   pdf -> page-aware chunks -> chroma
  graph.py        langgraph agent: retrieve -> grade -> answer or say "not enough context"
  summarize.py    problem/method/result summary from a paper's own chunks
  flashcards.py   study flashcards from a paper's own chunks
  llm.py          shared groq retry helper
  api.py          fastapi routes
```
