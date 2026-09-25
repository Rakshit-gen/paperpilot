import pytest


@pytest.fixture(autouse=True)
def _reset_vectorstore_singleton(monkeypatch):
    """get_vectorstore() caches a single client for the process's lifetime
    (see store.py). Tests force QDRANT_URL empty so they never touch the
    real cluster from .env, giving each test an isolated in-memory Qdrant
    instance; without the singleton reset, the first test to touch the
    vectorstore would leave every later test reusing the same in-memory
    collection instead of starting from empty.
    """
    import paperpilot.store as store

    monkeypatch.setattr(store, "QDRANT_URL", "")
    store._vectorstore = None
    yield
    store._vectorstore = None
