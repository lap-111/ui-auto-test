"""分类模块路由：增删改查。"""
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..config import SEED_BUGS
from ..db import get_db
from ..deps import require_user

router = APIRouter()


class CategoryPayload(BaseModel):
    name: str
    type: str = "expense"


def _duplicate_error() -> HTTPException:
    # 缺陷 D3：重名时返回笼统的"未知错误"而非明确提示
    if SEED_BUGS:
        return HTTPException(status_code=400, detail="未知错误")
    return HTTPException(status_code=400, detail="分类名称已存在")


def _ensure_category(db: sqlite3.Connection, user_id: int, category_id: int):
    row = db.execute(
        "SELECT * FROM categories WHERE id = ? AND user_id = ?",
        (category_id, user_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    return row


@router.get("")
def list_categories(
    type: str = Query(default=""),
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    sql = "SELECT * FROM categories WHERE user_id = ?"
    params: list = [user_id]
    if type in ("income", "expense"):
        sql += " AND type = ?"
        params.append(type)
    sql += " ORDER BY type, id"
    rows = db.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
def create_category(
    payload: CategoryPayload,
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="分类名称不能为空")
    if payload.type not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="分类类型不合法")
    dup = db.execute(
        "SELECT 1 FROM categories WHERE user_id = ? AND name = ?",
        (user_id, name),
    ).fetchone()
    if dup:
        raise _duplicate_error()
    cur = db.execute(
        "INSERT INTO categories (user_id, name, type) VALUES (?, ?, ?)",
        (user_id, name, payload.type),
    )
    db.commit()
    return {"id": cur.lastrowid, "name": name, "type": payload.type}


@router.put("/{category_id}")
def update_category(
    category_id: int,
    payload: CategoryPayload,
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    _ensure_category(db, user_id, category_id)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="分类名称不能为空")
    dup = db.execute(
        "SELECT 1 FROM categories WHERE user_id = ? AND name = ? AND id != ?",
        (user_id, name, category_id),
    ).fetchone()
    if dup:
        raise _duplicate_error()
    db.execute(
        "UPDATE categories SET name = ?, type = ? WHERE id = ?",
        (name, payload.type, category_id),
    )
    db.commit()
    return {"id": category_id, "name": name, "type": payload.type}


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    _ensure_category(db, user_id, category_id)
    has_bills = db.execute(
        "SELECT 1 FROM bills WHERE category_id = ?", (category_id,)
    ).fetchone()
    if has_bills:
        raise HTTPException(status_code=400, detail="该分类下存在账单，无法删除")
    db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    db.commit()
    return {"ok": True}
