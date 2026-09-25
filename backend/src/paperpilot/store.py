import hashlib
import os
import tarfile
from pathlib import Path

# onnxruntime's telemetry worker thread has a known crash-on-exit bug on
# macOS (a mutex it already tore down gets locked again during interpreter
# shutdown), which shows up as a Python crash report on every process exit.
# Disabling its telemetry before onnxruntime is imported avoids starting
# that thread in the first place.
os.environ.setdefault("ORT_DISABLE_TELEMETRY_EVENTS", "1")

import httpx
import numpy as np
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

_MODEL_DIR = Path.home() / ".cache" / "paperpilot" / "onnx_models" / "all-MiniLM-L6-v2"
_MODEL_FILES_DIR = _MODEL_DIR / "onnx"  # the archive's top-level entry is an "onnx/" dir
_MODEL_URL = "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"
_MODEL_SHA256 = "913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3"

_embeddings = None
_vectorstore = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _ensure_model_downloaded() -> None:
    if (_MODEL_FILES_DIR / "model.onnx").exists() and (_MODEL_FILES_DIR / "tokenizer.json").exists():
        return
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    archive = _MODEL_DIR / "onnx.tar.gz"
    with httpx.stream("GET", _MODEL_URL) as resp, open(archive, "wb") as f:
        for chunk in resp.iter_bytes(chunk_size=65536):
            f.write(chunk)
    if _sha256(archive) != _MODEL_SHA256:
        os.remove(archive)
        raise ValueError("all-MiniLM-L6-v2 ONNX download failed checksum verification")
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(_MODEL_DIR)
    os.remove(archive)


class _MiniLML6V2Embeddings(Embeddings):
    """Runs the same all-MiniLM-L6-v2 ONNX build chromadb ships, but through
    onnxruntime directly instead of through chromadb.

    chromadb.utils.embedding_functions.ONNXMiniLM_L6_V2 does the same
    inference, but importing it drags in chromadb's entire package (grpc,
    opentelemetry instrumentation, a kubernetes client, rich, pydantic
    settings -- ~850 modules) just for this one utility class. Combined with
    onnxruntime's default memory arena, that pushed peak RSS to ~780MB on
    the first embed call, past Render's 512MB limit regardless of which
    vector store sat behind it. Skipping chromadb and disabling the arena
    keeps the same model and tokenizer but keeps peak RSS around 230MB.
    """

    def __init__(self):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        _ensure_model_downloaded()

        so = ort.SessionOptions()
        so.log_severity_level = 3
        so.enable_cpu_mem_arena = False
        so.enable_mem_pattern = False
        so.intra_op_num_threads = 1
        so.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(_MODEL_FILES_DIR / "model.onnx"), providers=["CPUExecutionProvider"], sess_options=so
        )
        self._tokenizer = Tokenizer.from_file(str(_MODEL_FILES_DIR / "tokenizer.json"))
        # max_seq_length = 256: sentence-transformers uses 256 for this model
        # even though its HF config reports a max length of 128.
        self._tokenizer.enable_truncation(max_length=256)
        self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=256)

    def _run(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            encoded = [self._tokenizer.encode(t) for t in batch]
            input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
            attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
            token_type_ids = np.zeros_like(input_ids)
            last_hidden_state = self._session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids,
                },
            )[0]
            mask = np.broadcast_to(attention_mask[..., None], last_hidden_state.shape)
            pooled = np.sum(last_hidden_state * mask, axis=1) / np.clip(mask.sum(axis=1), 1e-9, None)
            norm = np.linalg.norm(pooled, axis=1)
            norm[norm == 0] = 1e-12
            all_embeddings.append((pooled / norm[:, None]).astype(np.float32))
        return np.concatenate(all_embeddings).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._run(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._run([text])[0]


def get_embeddings() -> Embeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = _MiniLML6V2Embeddings()
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
