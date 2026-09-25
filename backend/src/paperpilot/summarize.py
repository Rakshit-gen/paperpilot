from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from paperpilot.config import GROQ_MODEL, require_groq_key
from paperpilot.llm import invoke_with_retry
from paperpilot.registry import get_paper
from paperpilot.store import get_paper_chunks

SUMMARY_PROMPT = ChatPromptTemplate.from_template(
    """Summarize this paper in three short parts based only on the text
below, don't add anything the text doesn't support.

Problem: what problem is the paper addressing, in a sentence or two.
Method: what approach does it take, in a sentence or two.
Result: what did it find or conclude, in a sentence or two.

Paper text:
{context}

Write the summary as:
Problem: ...
Method: ...
Result: ..."""
)


def summarize_paper(paper_id: str) -> dict:
    paper = get_paper(paper_id)
    if paper is None:
        raise ValueError(f"no paper found with id {paper_id}")

    require_groq_key()
    chunks = get_paper_chunks(paper_id)
    if not chunks:
        raise ValueError(f"no chunks found for paper {paper_id}, was it ingested?")
    context = "\n\n".join(c["text"] for c in chunks)

    llm = ChatGroq(model=GROQ_MODEL, temperature=0)
    chain = SUMMARY_PROMPT | llm
    result = invoke_with_retry(chain, {"context": context})

    return {"paper_id": paper_id, "title": paper["title"], "summary": result.content}
