import logging
import os
import re
import tempfile
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator

from paperpilot.auth import (
    create_token,
    get_current_user_id,
    get_current_user_id_from_header_or_query,
    hash_password,
    verify_password,
)
from paperpilot.config import CORS_ORIGIN, UPLOAD_DIR
from paperpilot.db import init_db
from paperpilot.flashcards import generate_flashcards
from paperpilot.graph import ask as run_ask
from paperpilot.pdf_ingest import ingest_pdf
from paperpilot.registry import get_paper, list_papers
from paperpilot.summarize import summarize_paper
from paperpilot import sessions as sessions_store
from paperpilot.users import create_user, get_user_by_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("paperpilot.api")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25mb, papers are text, not scanned image dumps
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="paperpilot", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


class SignupRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("not a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def valid_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


def _auth_response(user: dict) -> dict:
    return {"token": create_token(user["id"]), "user": {"id": user["id"], "email": user["email"]}}


@app.post("/auth/signup")
def signup(req: SignupRequest) -> dict:
    if get_user_by_email(req.email) is not None:
        raise HTTPException(status_code=409, detail="an account with that email already exists")
    user = create_user(req.email, hash_password(req.password))
    return _auth_response(user)


@app.post("/auth/login")
def login(req: LoginRequest) -> dict:
    user = get_user_by_email(req.email.strip().lower())
    if user is None or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid email or password")
    return _auth_response(user)


@app.get("/auth/me")
def me(user_id: str = Depends(get_current_user_id)) -> dict:
    return {"user_id": user_id}


@app.get("/papers")
def get_papers(user_id: str = Depends(get_current_user_id)) -> dict:
    return {"papers": list_papers(user_id)}


@app.post("/papers/upload")
async def upload_paper(
    file: UploadFile = File(...), user_id: str = Depends(get_current_user_id)
) -> dict:
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
        result = ingest_pdf(
            tmp_path, user_id=user_id, title=os.path.splitext(file.filename)[0], filename=file.filename
        )
    except ValueError as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=400, detail=str(e))

    # keep the PDF around under its paper_id so /papers/{id}/file can serve it
    # for citation links to open the source document directly.
    persisted_path = os.path.join(UPLOAD_DIR, f"{result['paper_id']}.pdf")
    os.replace(tmp_path, persisted_path)

    logger.info("ingested paper %s (%d chunks)", result["title"], result["chunks"])
    return result


@app.get("/papers/{paper_id}/file")
def get_paper_file(
    paper_id: str, user_id: str = Depends(get_current_user_id_from_header_or_query)
) -> FileResponse:
    paper = get_paper(paper_id, user_id)
    if paper is None:
        raise HTTPException(status_code=404, detail=f"no paper found with id {paper_id}")
    path = os.path.join(UPLOAD_DIR, f"{paper_id}.pdf")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="source file is no longer on disk")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=paper["filename"],
        content_disposition_type="inline",
    )


class AskRequest(BaseModel):
    question: str
    paper_id: str | None = None
    session_id: str | None = None


@app.post("/ask")
def ask_question(req: AskRequest, user_id: str = Depends(get_current_user_id)) -> dict:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question can't be empty")
    try:
        result = run_ask(req.question, user_id=user_id, paper_id=req.paper_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if req.session_id:
        updated = sessions_store.add_message(req.session_id, user_id, req.question, result["answer"])
        if updated is None:
            raise HTTPException(status_code=404, detail=f"no session found with id {req.session_id}")

    return {"answer": result["answer"]}


@app.post("/papers/{paper_id}/summarize")
def summarize(paper_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    try:
        return summarize_paper(paper_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/papers/{paper_id}/flashcards")
def flashcards(paper_id: str, count: int = 5, user_id: str = Depends(get_current_user_id)) -> dict:
    try:
        return generate_flashcards(paper_id, user_id, count=count)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


class CreateSessionRequest(BaseModel):
    paper_id: str | None = None


@app.post("/sessions")
def create_session(req: CreateSessionRequest, user_id: str = Depends(get_current_user_id)) -> dict:
    return sessions_store.create_session(user_id, req.paper_id)


@app.get("/sessions")
def list_sessions(user_id: str = Depends(get_current_user_id)) -> dict:
    return {"sessions": sessions_store.list_sessions(user_id)}


@app.get("/sessions/{session_id}")
def get_session(session_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    session = sessions_store.get_session(session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"no session found with id {session_id}")
    return session


class RenameSessionRequest(BaseModel):
    title: str


@app.patch("/sessions/{session_id}")
def rename_session(
    session_id: str, req: RenameSessionRequest, user_id: str = Depends(get_current_user_id)
) -> dict:
    session = sessions_store.rename_session(session_id, user_id, req.title.strip() or "New chat")
    if session is None:
        raise HTTPException(status_code=404, detail=f"no session found with id {session_id}")
    return session


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    if not sessions_store.delete_session(session_id, user_id):
        raise HTTPException(status_code=404, detail=f"no session found with id {session_id}")
    return {"deleted": True}
