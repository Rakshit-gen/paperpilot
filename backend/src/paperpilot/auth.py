from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, Request

from paperpilot.config import SECRET_KEY
from paperpilot.users import get_user_by_id

JWT_ALGORITHM = "HS256"
JWT_EXPIRES_DAYS = 30


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRES_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def _user_id_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid or expired token")

    user_id = payload.get("sub")
    if not user_id or get_user_by_id(user_id) is None:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return user_id


def get_current_user_id(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid Authorization header")
    return _user_id_from_token(header.removeprefix("Bearer ").strip())


def get_current_user_id_from_header_or_query(request: Request, token: str | None = None) -> str:
    """Same as get_current_user_id, but also accepts ?token=... in the URL.

    Only for the PDF-serving endpoint: it's opened as a plain browser
    navigation (a link's target=_blank), which can't attach an
    Authorization header the way fetch() calls elsewhere can.
    """
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return _user_id_from_token(header.removeprefix("Bearer ").strip())
    if token:
        return _user_id_from_token(token)
    raise HTTPException(status_code=401, detail="missing or invalid token")
