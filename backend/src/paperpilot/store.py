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
