import os

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


def test_retrieve_node_finds_relevant_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path))

    from paperpilot.pdf_ingest import ingest_pdf
    from paperpilot.graph import retrieve_node

    path = os.path.join(SAMPLES_DIR, "cache-invalidation-postmortem-study.pdf")
    ingest_pdf(path)

    state = {"question": "how does jittering ttls help with cache stampedes", "paper_id": None}
    result = retrieve_node(state)

    assert len(result["retrieved"]) > 0
    assert any("jitter" in r["text"].lower() for r in result["retrieved"])


def test_retrieve_node_filters_by_paper_id(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path))

    from paperpilot.pdf_ingest import ingest_pdf
    from paperpilot.graph import retrieve_node

    r1 = ingest_pdf(os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf"))
    ingest_pdf(os.path.join(SAMPLES_DIR, "cache-invalidation-postmortem-study.pdf"))

    state = {"question": "explain the approach", "paper_id": r1["paper_id"]}
    result = retrieve_node(state)

    assert all(r["title"] == "attention-is-all-you-need-notes" for r in result["retrieved"])
