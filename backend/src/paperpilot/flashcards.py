from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from paperpilot.config import GROQ_MODEL, require_groq_key
from paperpilot.registry import get_paper
from paperpilot.store import get_paper_chunks

FLASHCARD_PROMPT = ChatPromptTemplate.from_template(
    """Write {count} study flashcards based only on the paper text below.
Each flashcard tests one specific idea from the text, not a vague
restatement of the title. Format each one on its own line exactly like
this, nothing else:

Q: <question> | A: <answer>

Paper text:
{context}"""
)


def _parse_flashcards(raw: str) -> list[dict]:
    cards = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line.startswith("Q:") or "| A:" not in line:
            continue
        question, answer = line[2:].split("| A:", 1)
        cards.append({"question": question.strip(), "answer": answer.strip()})
    return cards


def generate_flashcards(paper_id: str, count: int = 5) -> dict:
    paper = get_paper(paper_id)
    if paper is None:
        raise ValueError(f"no paper found with id {paper_id}")

    require_groq_key()
    chunks = get_paper_chunks(paper_id)
    if not chunks:
        raise ValueError(f"no chunks found for paper {paper_id}, was it ingested?")
    context = "\n\n".join(c["text"] for c in chunks)

    llm = ChatGroq(model=GROQ_MODEL, temperature=0.3)
    chain = FLASHCARD_PROMPT | llm
    result = chain.invoke({"context": context, "count": count})

    return {
        "paper_id": paper_id,
        "title": paper["title"],
        "flashcards": _parse_flashcards(result.content),
    }
