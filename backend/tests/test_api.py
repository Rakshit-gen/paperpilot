import io
import os

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


def _client(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setattr("paperpilot.api.UPLOAD_DIR", str(tmp_path / "uploads"))

    from fastapi.testclient import TestClient

    from paperpilot.api import app

    return TestClient(app)


def test_health(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_upload_rejects_non_pdf(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    r = client.post("/papers/upload", files={"file": ("notes.txt", io.BytesIO(b"hi"), "text/plain")})
    assert r.status_code == 400


def test_upload_stores_real_filename_not_temp_name(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    path = os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf")
    with open(path, "rb") as f:
        r = client.post("/papers/upload", files={"file": ("my-paper.pdf", f, "application/pdf")})
    assert r.status_code == 200

    papers = client.get("/papers").json()["papers"]
    assert papers[0]["filename"] == "my-paper.pdf"


def test_ask_empty_question_rejected(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    r = client.post("/ask", json={"question": "   "})
    assert r.status_code == 400


def test_summarize_missing_paper_404s(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    r = client.post("/papers/does-not-exist/summarize")
    assert r.status_code == 404
