import os

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")
USER_ID = "test-user"


def test_retrieve_node_finds_relevant_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.registry.DATA_DIR", str(tmp_path))

    from paperpilot.pdf_ingest import ingest_pdf
    from paperpilot.graph import retrieve_node

    path = os.path.join(SAMPLES_DIR, "cache-invalidation-postmortem-study.pdf")
    ingest_pdf(path, user_id=USER_ID)

    state = {"question": "how does jittering ttls help with cache stampedes", "paper_id": None, "user_id": USER_ID}
    result = retrieve_node(state)

    assert len(result["retrieved"]) > 0
    assert any("jitter" in r["text"].lower() for r in result["retrieved"])


def test_retrieve_node_filters_by_paper_id(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.registry.DATA_DIR", str(tmp_path))

    from paperpilot.pdf_ingest import ingest_pdf
    from paperpilot.graph import retrieve_node

    r1 = ingest_pdf(os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf"), user_id=USER_ID)
    ingest_pdf(os.path.join(SAMPLES_DIR, "cache-invalidation-postmortem-study.pdf"), user_id=USER_ID)

    state = {"question": "explain the approach", "paper_id": r1["paper_id"], "user_id": USER_ID}
    result = retrieve_node(state)

    assert all(r["title"] == "attention-is-all-you-need-notes" for r in result["retrieved"])


def test_retrieve_node_does_not_cross_user_boundaries(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.registry.DATA_DIR", str(tmp_path))

    from paperpilot.pdf_ingest import ingest_pdf
    from paperpilot.graph import retrieve_node

    ingest_pdf(
        os.path.join(SAMPLES_DIR, "cache-invalidation-postmortem-study.pdf"), user_id="user-a"
    )

    state = {
        "question": "how does jittering ttls help with cache stampedes",
        "paper_id": None,
        "user_id": "user-b",
    }
    result = retrieve_node(state)

    assert result["retrieved"] == []
