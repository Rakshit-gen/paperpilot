import os
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from paperpilot.config import CHUNK_OVERLAP, CHUNK_SIZE
from paperpilot.registry import add_paper
from paperpilot.store import get_vectorstore


def _read_pages(path: str) -> list[str]:
    reader = PdfReader(path)
    return [page.extract_text() or "" for page in reader.pages]


def ingest_pdf(path: str, user_id: str, title: str | None = None, filename: str | None = None) -> dict:
    """Chunk a PDF page by page and store it with page-level citations.

    Chunking per page (instead of the whole document at once) keeps the
    page number attached to every chunk, which is the entire point of
    this tool: an answer has to point back to an exact page, not just
    "somewhere in this paper".

    filename defaults to path's basename, but callers that ingest from a
    temp file (like the upload endpoint, which can't keep the original
    filename on disk) should pass the real original filename explicitly,
    otherwise the registry ends up recording a random temp file name.
    """
    pages = _read_pages(path)
    if not any(p.strip() for p in pages):
        raise ValueError(f"No extractable text found in {path}")

    paper_id = str(uuid.uuid4())[:8]
    filename = filename or os.path.basename(path)
    display_title = title or os.path.splitext(filename)[0]

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    texts, metadatas, ids = [], [], []
    for page_num, page_text in enumerate(pages, start=1):
        if not page_text.strip():
            continue
        for i, chunk in enumerate(splitter.split_text(page_text)):
            texts.append(chunk)
            metadatas.append(
                {
                    "paper_id": paper_id,
                    "user_id": user_id,
                    "title": display_title,
                    "page": page_num,
                }
            )
            ids.append(f"{paper_id}::{page_num}::{i}")

    store = get_vectorstore()
    store.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    add_paper(paper_id=paper_id, user_id=user_id, title=display_title, filename=filename, page_count=len(pages))

    return {"paper_id": paper_id, "title": display_title, "chunks": len(texts), "pages": len(pages)}
