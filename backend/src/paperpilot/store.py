import os

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
# chromadb pulls in onnxruntime even though we never use its default
# embedding function. onnxruntime's own telemetry worker thread has a
# known crash-on-exit bug on macOS (a mutex it already tore down gets
# locked again during interpreter shutdown), which shows up as a Python
# crash report on every process exit. Disabling its telemetry before
# chromadb imports it avoids starting that thread in the first place.
os.environ.setdefault("ORT_DISABLE_TELEMETRY_EVENTS", "1")

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from paperpilot.config import CHROMA_DIR, EMBEDDING_MODEL

_embeddings = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"}
        )
    return _embeddings


def get_vectorstore() -> Chroma:
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=get_embeddings())


def get_paper_chunks(paper_id: str) -> list[dict]:
    """Fetch every chunk for a paper, in page order.

    A similarity search against some proxy query would only surface the
    chunks closest to that query, not the whole paper, so summarizing or
    generating flashcards needs a direct metadata lookup instead.
    """
    store = get_vectorstore()
    result = store._collection.get(where={"paper_id": paper_id}, include=["documents", "metadatas"])
    chunks = [
        {"text": doc, "page": meta.get("page", 0)}
        for doc, meta in zip(result["documents"], result["metadatas"])
    ]
    return sorted(chunks, key=lambda c: c["page"])
