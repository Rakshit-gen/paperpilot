# paperpilot

Anyone doing a literature review ends up with thirty PDFs open and no fast
way to ask "what did paper four actually say about this" without
re-reading it. paperpilot fixes that: upload your papers, ask questions
across the whole pile in plain language, and get an answer with the exact
paper and page it came from, not a vague paraphrase you have to go verify
yourself.

It also generates a structured summary card per paper (problem, method,
result) and a set of flashcards for review, both grounded in the actual
text instead of a generic template.

## Why this matters for research specifically

Citations aren't a nice-to-have here, they're the whole point. A research
tool that gives you an answer with no way to check where it came from is
not more useful than not using it, you still have to go re-read the paper
to trust the answer. Every answer paperpilot gives points back to the
exact source.

## How it's built

- `backend/`: a FastAPI service. Ingests PDFs into a Chroma vector store,
  and runs a LangGraph agent for question answering: retrieve chunks,
  grade whether they actually answer the question, and either answer with
  citations or say plainly that the library doesn't have enough to answer
  instead of guessing. Summaries and flashcards are separate LangChain
  chains grounded in a paper's own chunks. Groq is the LLM throughout.
- `frontend/`: a Next.js app with shadcn/ui, the actual interface people
  use, upload papers, ask questions, read summaries and flashcards.

See `backend/README.md` and `frontend/README.md` for setup.
