"""One-off script to generate the sample PDFs checked into samples/.

Not part of the app, just how those fixture files were created. Requires
fpdf2, which is not a runtime dependency of paperpilot itself.
"""

from fpdf import FPDF

PAPERS = {
    "attention-is-all-you-need-notes.pdf": [
        (
            "Attention Mechanisms in Sequence Models (study notes)\n\n"
            "Problem: recurrent models process sequences step by step, which "
            "makes them slow to train and makes it hard for information from "
            "early in a long sequence to influence predictions much later on. "
            "This is often called the long range dependency problem.\n\n"
            "The core idea covered in these notes is self-attention: instead "
            "of processing tokens strictly in order, every token attends "
            "directly to every other token in the sequence in a single step. "
            "Each token produces a query, a key, and a value vector. The "
            "attention weight between two tokens comes from the dot product "
            "of one token's query with another's key, scaled and passed "
            "through softmax, and the output is a weighted sum of value "
            "vectors."
        ),
        (
            "Multi head attention runs several attention operations in "
            "parallel with different learned projections, then concatenates "
            "the results. The intuition is that different heads can "
            "specialize, one might track subject verb agreement, another "
            "might track coreference, without anyone hand designing that "
            "split.\n\n"
            "Method summary: stack multi head self attention layers with "
            "feed forward layers and residual connections, no recurrence at "
            "all. Position information is added explicitly since attention "
            "itself has no notion of order.\n\n"
            "Result summary: this architecture trained faster than "
            "recurrent alternatives on the tasks tested and reached better "
            "quality, largely because the full sequence can be processed in "
            "parallel instead of one step at a time."
        ),
    ],
    "cache-invalidation-postmortem-study.pdf": [
        (
            "Distributed Cache Invalidation, a review of failure patterns\n\n"
            "Problem: keeping a distributed cache consistent with its "
            "source of truth is hard because invalidation messages can "
            "arrive out of order, get dropped, or race with a write that "
            "happens right after the cache was refreshed.\n\n"
            "This note reviews three recurring failure patterns seen across "
            "several postmortems: the thundering herd on simultaneous "
            "expiry, the stale read after a write due to invalidation "
            "lag, and the invalidation storm where a burst of writes "
            "triggers more invalidation traffic than the cache tier can "
            "absorb."
        ),
        (
            "Method: for the thundering herd pattern, adding random jitter "
            "to TTLs spreads out expiry so instances don't all miss the "
            "cache at the same instant. For stale reads after a write, "
            "writing through the cache synchronously (updating the cache in "
            "the same request that updates the source of truth) closes the "
            "window instead of relying on a separate invalidation message "
            "arriving in time.\n\n"
            "Result: teams that moved from time based invalidation alone to "
            "a mix of jittered TTLs and write through updates saw "
            "meaningfully fewer stale read incidents, though write through "
            "does add latency to the write path that has to be budgeted "
            "for."
        ),
    ],
}


def make_pdf(path: str, pages: list[str]) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for page_text in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6, page_text)
    pdf.output(path)


if __name__ == "__main__":
    import os

    out_dir = os.path.join(os.path.dirname(__file__), "..", "samples")
    os.makedirs(out_dir, exist_ok=True)
    for filename, pages in PAPERS.items():
        path = os.path.join(out_dir, filename)
        make_pdf(path, pages)
        print(f"wrote {path}")
