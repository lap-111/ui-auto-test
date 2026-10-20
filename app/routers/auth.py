"""用户模块路由：注册、登录、登出、改密。"""
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import get_db
from ..deps import require_user
from ..security import create_token, hash_password, verify_password

router = APIRouter()


class AuthPayload(BaseModel):
    username: str
    password: str


class PasswordPayload(BaseModel):
    old_password: str
    new_password: str


@router.post("/register", status_code=201)
def register(payload: AuthPayload, db: sqlite3.Connection = Depends(get_db)):
    username = payload.username.strip()
    if not username or not payload.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    exists = db.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    ).fetchone()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    cur = db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, hash_password(payload.password)),
    )
    db.commit()
    return {"id": cur.lastrowid, "username": username}


@router.post("/login")
def login(payload: AuthPayload, db: sqlite3.Connection = Depends(get_db)):
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (payload.username.strip(),)
    ).fetchone()
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(db, user["id"])
    return {"token": token, "username": user["username"]}


@router.post("/logout")
def logout(
    x_token: str = "",
    db: sqlite3.Connection = Depends(get_db),
):
    if x_token:
        db.execute("DELETE FROM sessions WHERE token = ?", (x_token,))
        db.commit()
    return {"ok": True}


@router.get("/me")
def me(
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    user = db.execute(
        "SELECT id, username, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return dict(user)


@router.put("/password")
def change_password(
    payload: PasswordPayload,
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    user = db.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not verify_password(payload.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="原密码错误")
    if not payload.new_password:
        raise HTTPException(status_code=400, detail="新密码不能为空")
    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(payload.new_password), user_id),
    )
    # 改密后使所有会话失效
    db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    db.commit()
    return {"ok": True}
