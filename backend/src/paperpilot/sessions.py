import uuid
from datetime import datetime, timezone

from paperpilot.db import connect

TITLE_PREVIEW_LEN = 60


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session(user_id: str, paper_id: str | None) -> dict:
    session = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "paper_id": paper_id,
        "title": "New chat",
        "created_at": _now(),
        "updated_at": _now(),
    }
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (id, user_id, paper_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                session["id"],
                session["user_id"],
                session["paper_id"],
                session["title"],
                session["created_at"],
                session["updated_at"],
            ),
        )
    return session


def list_sessions(user_id: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_session(session_id: str, user_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id)
        ).fetchone()
        if row is None:
            return None
        session = dict(row)
        messages = conn.execute(
            "SELECT question, answer, created_at FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        session["messages"] = [dict(m) for m in messages]
        return session


def rename_session(session_id: str, user_id: str, title: str) -> dict | None:
    with connect() as conn:
        conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (title, _now(), session_id, user_id),
        )
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def delete_session(session_id: str, user_id: str) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id)
        )
        return cur.rowcount > 0


def add_message(session_id: str, user_id: str, question: str, answer: str) -> dict | None:
    with connect() as conn:
        session = conn.execute(
            "SELECT * FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id)
        ).fetchone()
        if session is None:
            return None
        conn.execute(
            "INSERT INTO messages (session_id, question, answer, created_at) VALUES (?, ?, ?, ?)",
            (session_id, question, answer, _now()),
        )
        # auto-title the session from its first question, chatgpt-style
        title = session["title"]
        if title == "New chat":
            title = question if len(question) <= TITLE_PREVIEW_LEN else question[:TITLE_PREVIEW_LEN].rstrip() + "..."
        conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title, _now(), session_id),
        )
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row)
