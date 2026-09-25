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
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    VectorParams,
)

from paperpilot.config import QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL

_EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output size

_embeddings = None
_vectorstore = None


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


def get_vectorstore() -> QdrantVectorStore:
    """Return a single shared Qdrant-backed vector store for the process's lifetime.

    Chroma kept its whole HNSW index resident in the API process, so memory
    grew with every upload no matter how the client was reused, until the
    process got OOM-killed on Render's 512MB free tier. Qdrant Cloud holds
    the index instead, so the process only ever holds one request's worth of
    vectors in memory at a time. QDRANT_URL unset (local dev/tests) falls
    back to an in-memory Qdrant instance instead of a real cluster.
    """
    global _vectorstore
    if _vectorstore is None:
        client = (
            QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
            if QDRANT_URL
            else QdrantClient(location=":memory:")
        )
        if not client.collection_exists(QDRANT_COLLECTION):
            client.create_collection(
                QDRANT_COLLECTION,
                vectors_config=VectorParams(size=_EMBEDDING_DIM, distance=Distance.COSINE),
            )
            # Unlike Chroma, Qdrant refuses to filter on a payload field
            # until it has an index for it.
            for field in ("metadata.paper_id", "metadata.user_id"):
                client.create_payload_index(
                    QDRANT_COLLECTION, field_name=field, field_schema=PayloadSchemaType.KEYWORD
                )
        _vectorstore = QdrantVectorStore(
            client=client, collection_name=QDRANT_COLLECTION, embedding=get_embeddings()
        )
    return _vectorstore


def get_paper_chunks(paper_id: str, user_id: str) -> list[dict]:
    """Fetch every chunk for a paper, in page order.

    A similarity search against some proxy query would only surface the
    chunks closest to that query, not the whole paper, so summarizing or
    generating flashcards needs a direct metadata lookup instead.
    """
    store = get_vectorstore()
    records, _ = store.client.scroll(
        collection_name=QDRANT_COLLECTION,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="metadata.paper_id", match=MatchValue(value=paper_id)),
                FieldCondition(key="metadata.user_id", match=MatchValue(value=user_id)),
            ]
        ),
        limit=10_000,
        with_payload=True,
    )
    chunks = [
        {"text": r.payload["page_content"], "page": r.payload["metadata"].get("page", 0)}
        for r in records
    ]
    return sorted(chunks, key=lambda c: c["page"])
