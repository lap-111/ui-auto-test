"""FastAPI 公共依赖。"""
import sqlite3

from fastapi import Depends, Header, HTTPException

from .db import get_db
from .security import get_user_id


def require_user(
    x_token: str = Header(default=""),
    db: sqlite3.Connection = Depends(get_db),
) -> int:
    """校验登录态，返回 user_id。"""
    user_id = get_user_id(db, x_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return user_id
