import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


load_dotenv()

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
DATABASE_PATH = Path(os.getenv("AUTH_DATABASE_PATH", Path(__file__).resolve().parents[1] / "auth.db"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _get_secret_key() -> str:
    secret_key = os.getenv("JWT_SECRET_KEY")
    if not secret_key or len(secret_key) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be configured with at least 32 characters.")
    return secret_key


def init_auth_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            )
            """
        )


def _hash_password(password: str, salt: bytes | None = None) -> str:
    password_salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), password_salt, 310_000)
    return f"{password_salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, digest_hex = stored_hash.split("$", 1)
    expected = _hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
    return hmac.compare_digest(expected, digest_hex)


def _user_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {"id": row["id"], "username": row["username"], "role": row["role"]}


def create_user(username: str, password: str) -> dict[str, Any]:
    init_auth_database()
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username.strip().lower(), _hash_password(password), datetime.now(timezone.utc).isoformat()),
            )
            row = connection.execute("SELECT id, username, role FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Username is already registered.") from error

    return _user_from_row(row)


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    init_auth_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()

    if row is None or not _verify_password(password, row["password_hash"]):
        return None
    return _user_from_row(row)


def create_access_token(user: dict[str, Any]) -> tuple[str, int]:
    expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _get_secret_key(), algorithm=JWT_ALGORITHM), expires_in


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub", ""))
    except (jwt.InvalidTokenError, TypeError, ValueError, RuntimeError) as error:
        raise credentials_error from error

    init_auth_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()

    if row is None:
        raise credentials_error
    return _user_from_row(row)


def require_role(required_role: str):
    def role_dependency(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user["role"] != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
        return current_user

    return role_dependency