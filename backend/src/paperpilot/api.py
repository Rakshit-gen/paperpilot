import logging
import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from paperpilot.config import CORS_ORIGIN, UPLOAD_DIR
from paperpilot.flashcards import generate_flashcards
from paperpilot.graph import ask as run_ask
from paperpilot.pdf_ingest import ingest_pdf
from paperpilot.registry import list_papers
from paperpilot.summarize import summarize_paper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("paperpilot.api")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25mb, papers are text, not scanned image dumps

app = FastAPI(title="paperpilot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/papers")
def get_papers() -> dict:
    return {"papers": list_papers()}


@app.post("/papers/upload")
async def upload_paper(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="only .pdf files are accepted")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, suffix=".pdf", delete=False) as tmp:
        size = 0
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                tmp.close()
                os.remove(tmp.name)
                raise HTTPException(status_code=413, detail="file too large, 25mb max")
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        result = ingest_pdf(tmp_path, title=os.path.splitext(file.filename)[0], filename=file.filename)
        logger.info("ingested paper %s (%d chunks)", result["title"], result["chunks"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class AskRequest(BaseModel):
    question: str
    paper_id: str | None = None


@app.post("/ask")
def ask_question(req: AskRequest) -> dict:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question can't be empty")
    try:
        result = run_ask(req.question, paper_id=req.paper_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"answer": result["answer"]}


@app.post("/papers/{paper_id}/summarize")
def summarize(paper_id: str) -> dict:
    try:
        return summarize_paper(paper_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/papers/{paper_id}/flashcards")
def flashcards(paper_id: str, count: int = 5) -> dict:
    try:
        return generate_flashcards(paper_id, count=count)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
