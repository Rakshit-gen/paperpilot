import pytest


@pytest.fixture(autouse=True)
def _reset_vectorstore_singleton():
    """Each test points paperpilot.store.CHROMA_DIR at its own tmp_path, but
    get_vectorstore() caches a single Chroma client for the process's
    lifetime (see store.py). Without this, the first test to touch the
    vectorstore would leave every later test reusing a client pointed at a
    directory that no longer matches its own CHROMA_DIR patch.
    """
    import paperpilot.store as store

    store._vectorstore = None
    yield
    store._vectorstore = None
