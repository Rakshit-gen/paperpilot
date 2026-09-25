import os

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
# chromadb pulls in onnxruntime even though we never use its default
# embedding function. onnxruntime's own telemetry worker thread has a
# known crash-on-exit bug on macOS (a mutex it already tore down gets
# locked again during interpreter shutdown), which shows up as a Python
# crash report on every process exit. Disabling its telemetry before
# chromadb imports it avoids starting that thread in the first place.
os.environ.setdefault("ORT_DISABLE_TELEMETRY_EVENTS", "1")

from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from paperpilot.config import CHROMA_DIR

_embeddings = None


class _ChromaONNXEmbeddings(Embeddings):
    """Wraps chromadb's bundled ONNX all-MiniLM-L6-v2 as a langchain Embeddings.

    sentence-transformers pulls in torch, which alone pushes memory well past
    a 512MB free-tier instance. chromadb already ships onnxruntime as a
    dependency, and its ONNX build of the same all-MiniLM-L6-v2 model gets
    the same embeddings for a fraction of the memory.
    """

    def __init__(self):
        self._fn = ONNXMiniLM_L6_V2()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._fn(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self._fn([text])[0].tolist()


def get_embeddings() -> Embeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = _ChromaONNXEmbeddings()
    return _embeddings


def get_vectorstore() -> Chroma:
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=get_embeddings())


def get_paper_chunks(paper_id: str, user_id: str) -> list[dict]:
    """Fetch every chunk for a paper, in page order.

    A similarity search against some proxy query would only surface the
    chunks closest to that query, not the whole paper, so summarizing or
    generating flashcards needs a direct metadata lookup instead.
    """
    store = get_vectorstore()
    result = store._collection.get(
        where={"$and": [{"paper_id": paper_id}, {"user_id": user_id}]},
        include=["documents", "metadatas"],
    )
    chunks = [
        {"text": doc, "page": meta.get("page", 0)}
        for doc, meta in zip(result["documents"], result["metadatas"])
    ]
    return sorted(chunks, key=lambda c: c["page"])
