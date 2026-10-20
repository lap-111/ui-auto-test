"""安全模块：密码哈希与会话令牌。"""
import hashlib
import secrets
import sqlite3


def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    return hashlib.sha256((salt + password).encode()).hexdigest() == digest


def create_token(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_hex(24)
    conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
    conn.commit()
    return token


def get_user_id(conn: sqlite3.Connection, token: str):
    row = conn.execute("SELECT user_id FROM sessions WHERE token = ?", (token,)).fetchone()
    return row["user_id"] if row else None
