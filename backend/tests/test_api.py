import io
import os

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


def _client(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setattr("paperpilot.api.UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr("paperpilot.db.DB_PATH", str(tmp_path / "test.db"))

    from fastapi.testclient import TestClient

    from paperpilot.api import app
    from paperpilot.db import init_db

    init_db()
    return TestClient(app)


def _auth_headers(client, email="reader@example.com", password="hunter22"):
    r = client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_signup_then_login_round_trip(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    r = client.post("/auth/signup", json={"email": "a@b.com", "password": "hunter22"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "a@b.com"

    r = client.post("/auth/login", json={"email": "a@b.com", "password": "hunter22"})
    assert r.status_code == 200
    assert "token" in r.json()

    r = client.post("/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert r.status_code == 401


def test_signup_rejects_duplicate_email(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/auth/signup", json={"email": "a@b.com", "password": "hunter22"})
    r = client.post("/auth/signup", json={"email": "a@b.com", "password": "hunter22"})
    assert r.status_code == 409


def test_endpoints_require_auth(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    assert client.get("/papers").status_code == 401
    assert client.post("/ask", json={"question": "hi"}).status_code == 401


def test_upload_rejects_non_pdf(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    r = client.post(
        "/papers/upload",
        files={"file": ("notes.txt", io.BytesIO(b"hi"), "text/plain")},
        headers=headers,
    )
    assert r.status_code == 400


def test_upload_stores_real_filename_not_temp_name(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    path = os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf")
    with open(path, "rb") as f:
        r = client.post(
            "/papers/upload", files={"file": ("my-paper.pdf", f, "application/pdf")}, headers=headers
        )
    assert r.status_code == 200

    papers = client.get("/papers", headers=headers).json()["papers"]
    assert papers[0]["filename"] == "my-paper.pdf"


def test_papers_are_scoped_per_user(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers_a = _auth_headers(client, email="a@example.com")
    headers_b = _auth_headers(client, email="b@example.com")
    path = os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf")
    with open(path, "rb") as f:
        client.post("/papers/upload", files={"file": ("a.pdf", f, "application/pdf")}, headers=headers_a)

    assert len(client.get("/papers", headers=headers_a).json()["papers"]) == 1
    assert len(client.get("/papers", headers=headers_b).json()["papers"]) == 0


def test_uploaded_pdf_is_served_back_for_citation_links(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    path = os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf")
    with open(path, "rb") as f:
        r = client.post(
            "/papers/upload", files={"file": ("attention.pdf", f, "application/pdf")}, headers=headers
        )
    paper_id = r.json()["paper_id"]

    r = client.get(f"/papers/{paper_id}/file", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")


def test_paper_file_404s_for_unknown_paper(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    r = client.get("/papers/does-not-exist/file", headers=headers)
    assert r.status_code == 404


def test_paper_file_accepts_token_query_param_for_plain_links(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    token = headers["Authorization"].removeprefix("Bearer ")
    path = os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf")
    with open(path, "rb") as f:
        r = client.post(
            "/papers/upload", files={"file": ("attention.pdf", f, "application/pdf")}, headers=headers
        )
    paper_id = r.json()["paper_id"]

    r = client.get(f"/papers/{paper_id}/file?token={token}")
    assert r.status_code == 200


def test_ask_empty_question_rejected(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    r = client.post("/ask", json={"question": "   "}, headers=headers)
    assert r.status_code == 400


def test_summarize_missing_paper_404s(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    r = client.post("/papers/does-not-exist/summarize", headers=headers)
    assert r.status_code == 404


def test_session_lifecycle(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers = _auth_headers(client)

    r = client.post("/sessions", json={"paper_id": None}, headers=headers)
    assert r.status_code == 200
    session = r.json()
    assert session["title"] == "New chat"

    r = client.get("/sessions", headers=headers)
    assert len(r.json()["sessions"]) == 1

    r = client.patch(f"/sessions/{session['id']}", json={"title": "renamed"}, headers=headers)
    assert r.json()["title"] == "renamed"

    r = client.delete(f"/sessions/{session['id']}", headers=headers)
    assert r.status_code == 200
    assert client.get("/sessions", headers=headers).json()["sessions"] == []


def test_sessions_are_scoped_per_user(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    headers_a = _auth_headers(client, email="a@example.com")
    headers_b = _auth_headers(client, email="b@example.com")

    client.post("/sessions", json={"paper_id": None}, headers=headers_a)
    assert len(client.get("/sessions", headers=headers_a).json()["sessions"]) == 1
    assert len(client.get("/sessions", headers=headers_b).json()["sessions"]) == 0
