from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from paperpilot.config import GROQ_MODEL, require_groq_key
from paperpilot.store import get_vectorstore

GRADE_PROMPT = ChatPromptTemplate.from_template(
    """You are checking whether retrieved text actually contains enough
information to answer a question. Answer with exactly one word, either
"yes" or "no".

Question: {question}

Retrieved text:
{context}

Does the retrieved text contain enough information to answer the
question? Answer yes or no:"""
)

ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """Answer the question using only the context below. After each claim,
cite the source in brackets like [paper title, page N]. Be precise, don't
pad the answer with things the context doesn't actually say.

Context:
{context}

Question: {question}

Answer:"""
)


class AskState(TypedDict):
    question: str
    paper_id: str | None
    retrieved: list[dict]
    is_relevant: bool
    answer: str


def retrieve_node(state: AskState) -> dict:
    store = get_vectorstore()
    filter_arg = {"paper_id": state["paper_id"]} if state.get("paper_id") else None
    docs = store.similarity_search(state["question"], k=5, filter=filter_arg)
    retrieved = [
        {"text": d.page_content, "title": d.metadata.get("title"), "page": d.metadata.get("page")}
        for d in docs
    ]
    return {"retrieved": retrieved}


def _format_context(retrieved: list[dict]) -> str:
    return "\n\n".join(f"[{r['title']}, page {r['page']}]\n{r['text']}" for r in retrieved)


def grade_node(state: AskState) -> dict:
    if not state["retrieved"]:
        return {"is_relevant": False}

    require_groq_key()
    llm = ChatGroq(model=GROQ_MODEL, temperature=0)
    chain = GRADE_PROMPT | llm
    result = chain.invoke(
        {"question": state["question"], "context": _format_context(state["retrieved"])}
    )
    return {"is_relevant": "yes" in result.content.strip().lower()}


def route_after_grade(state: AskState) -> str:
    return "generate_answer" if state["is_relevant"] else "insufficient_context"


def generate_answer_node(state: AskState) -> dict:
    require_groq_key()
    llm = ChatGroq(model=GROQ_MODEL, temperature=0)
    chain = ANSWER_PROMPT | llm
    result = chain.invoke(
        {"question": state["question"], "context": _format_context(state["retrieved"])}
    )
    return {"answer": result.content}


def insufficient_context_node(state: AskState) -> dict:
    return {
        "answer": (
            "I don't have enough information in your paper library to "
            "answer that. Try uploading a paper that covers this, or "
            "rephrase the question."
        )
    }


def build_graph():
    builder = StateGraph(AskState)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("grade", grade_node)
    builder.add_node("generate_answer", generate_answer_node)
    builder.add_node("insufficient_context", insufficient_context_node)

    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "grade")
    builder.add_conditional_edges(
        "grade",
        route_after_grade,
        {"generate_answer": "generate_answer", "insufficient_context": "insufficient_context"},
    )
    builder.add_edge("generate_answer", END)
    builder.add_edge("insufficient_context", END)

    return builder.compile()


def ask(question: str, paper_id: str | None = None) -> AskState:
    graph = build_graph()
    return graph.invoke(
        {
            "question": question,
            "paper_id": paper_id,
            "retrieved": [],
            "is_relevant": False,
            "answer": "",
        }
    )
