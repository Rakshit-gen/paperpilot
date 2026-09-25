import json
import os
import threading
from datetime import datetime, timezone

from paperpilot.config import DATA_DIR

_lock = threading.Lock()


def _registry_path() -> str:
    return os.path.join(DATA_DIR, "papers.json")


def _read_all() -> list[dict]:
    path = _registry_path()
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def _write_all(papers: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(_registry_path(), "w") as f:
        json.dump(papers, f, indent=2)


def add_paper(paper_id: str, user_id: str, title: str, filename: str, page_count: int) -> dict:
    """Register a paper's metadata.

    The vector store doesn't give a clean way to list distinct documents by
    metadata, so a small JSON sidecar file tracks the papers list. A real
    database would replace this, but a file lock is enough for a
    single-process FastAPI app.
    """
    record = {
        "paper_id": paper_id,
        "user_id": user_id,
        "title": title,
        "filename": filename,
        "page_count": page_count,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    with _lock:
        papers = _read_all()
        papers = [p for p in papers if p["paper_id"] != paper_id]
        papers.append(record)
        _write_all(papers)
    return record


def list_papers(user_id: str) -> list[dict]:
    with _lock:
        return [p for p in _read_all() if p["user_id"] == user_id]


def get_paper(paper_id: str, user_id: str) -> dict | None:
    for paper in list_papers(user_id):
        if paper["paper_id"] == paper_id:
            return paper
    return None
