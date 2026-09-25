import os

import pytest

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


def _ingest_sample(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path))
    from paperpilot.pdf_ingest import ingest_pdf

    return ingest_pdf(os.path.join(SAMPLES_DIR, "attention-is-all-you-need-notes.pdf"))


def test_get_paper_chunks_returns_all_chunks_in_page_order(tmp_path, monkeypatch):
    result = _ingest_sample(tmp_path, monkeypatch)
    from paperpilot.store import get_paper_chunks

    chunks = get_paper_chunks(result["paper_id"])
    assert len(chunks) == result["chunks"]
    pages = [c["page"] for c in chunks]
    assert pages == sorted(pages)


def test_summarize_paper_raises_on_unknown_paper(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path))
    from paperpilot.summarize import summarize_paper

    with pytest.raises(ValueError):
        summarize_paper("does-not-exist")


def test_generate_flashcards_raises_on_unknown_paper(tmp_path, monkeypatch):
    monkeypatch.setattr("paperpilot.store.CHROMA_DIR", str(tmp_path))
    monkeypatch.setattr("paperpilot.registry.CHROMA_DIR", str(tmp_path))
    from paperpilot.flashcards import generate_flashcards

    with pytest.raises(ValueError):
        generate_flashcards("does-not-exist")


def test_summarize_paper_fails_without_groq_key(tmp_path, monkeypatch):
    result = _ingest_sample(tmp_path, monkeypatch)
    monkeypatch.setattr("paperpilot.config.GROQ_API_KEY", "")
    from paperpilot.summarize import summarize_paper

    with pytest.raises(RuntimeError):
        summarize_paper(result["paper_id"])


def test_parse_flashcards_handles_well_formed_lines():
    from paperpilot.flashcards import _parse_flashcards

    raw = "Q: what is X? | A: X is Y\nQ: what is Z? | A: Z is W\nsome stray line"
    cards = _parse_flashcards(raw)

    assert len(cards) == 2
    assert cards[0] == {"question": "what is X?", "answer": "X is Y"}
