# paperpilot frontend

Next.js + shadcn/ui interface for paperpilot. Upload papers, ask questions
scoped to your whole library or a single paper, and generate summaries and
flashcards, all backed by the FastAPI service in `../backend`.

## Setup

```
cd frontend
npm install
cp .env.local.example .env.local   # points at the backend, defaults to localhost:8000
npm run dev
```

The backend needs to be running (see `../backend/README.md`) for anything
beyond the empty-state UI to work.

## Layout

```
src/
  app/page.tsx                the whole app: sidebar + tabs, client-rendered
  app/layout.tsx               fonts, metadata, toast host
  components/paper-sidebar.tsx library list + upload trigger
  components/upload-dialog.tsx drag-and-drop pdf upload
  components/ask-panel.tsx     chat-style Q&A with the corrective RAG backend
  components/summary-panel.tsx problem / method / result cards
  components/flashcards-panel.tsx flip-to-reveal study cards
  lib/api.ts                   typed fetch wrapper for the backend
```

No client-side state library, no routing beyond the single page. The app is
small enough that `useState` in `page.tsx` plus a shared `fetch` wrapper is
the whole data layer.
