import os

import pytest

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


def test_ingest_pdf_stores_page_level_citations(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path))

    from paperpilot.pdf_ingest import ingest_pdf
    from paperpilot.registry import get_paper
    from paperpilot.store import get_vectorstore

    path = os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf")
    result = ingest_pdf(path)

    assert result["chunks"] > 0
    assert result["pages"] == 2

    paper = get_paper(result["paper_id"])
    assert paper is not None
    assert paper["title"] == "attention-is-all-you-need-notes"

    store = get_vectorstore()
    docs = store.similarity_search("self attention query key value", k=2)
    assert docs
    assert docs[0].metadata["paper_id"] == result["paper_id"]
    assert docs[0].metadata["page"] in (1, 2)


def test_ingest_pdf_uses_explicit_filename_over_path_basename(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path))

    from paperpilot.pdf_ingest import ingest_pdf
    from paperpilot.registry import get_paper

    path = os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf")
    result = ingest_pdf(path, filename="original-upload-name.pdf")

    paper = get_paper(result["paper_id"])
    assert paper["filename"] == "original-upload-name.pdf"


def test_ingest_pdf_raises_on_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path))

    from paperpilot.pdf_ingest import ingest_pdf

    with pytest.raises(Exception):
        ingest_pdf(os.path.join(SAMPLES_DIR, "does-not-exist.pdf"))
