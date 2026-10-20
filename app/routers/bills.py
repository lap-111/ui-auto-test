"""记账模块路由：增删改查、筛选、分页。"""
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..config import SEED_BUGS
from ..db import get_db
from ..deps import require_user

router = APIRouter()


class BillPayload(BaseModel):
    category_id: int
    amount: float
    note: str = ""
    bill_date: str


def _category_row(db: sqlite3.Connection, user_id: int, category_id: int):
    row = db.execute(
        "SELECT * FROM categories WHERE id = ? AND user_id = ?",
        (category_id, user_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=400, detail="分类不存在")
    return row


def _upsert_summary(
    db: sqlite3.Connection, user_id: int, month: str, income: float, expense: float
) -> None:
    db.execute(
        """
        INSERT INTO monthly_summary (user_id, month, income, expense)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, month)
        DO UPDATE SET
            income = income + excluded.income,
            expense = expense + excluded.expense
        """,
        (user_id, month, income, expense),
    )


def _validate_amount(amount: float) -> float:
    if amount is None or amount <= 0:
        raise HTTPException(status_code=400, detail="金额必须大于 0")
    return round(float(amount), 2)


@router.get("")
def list_bills(
    category_id: int = Query(default=0),
    type: str = Query(default=""),
    month: str = Query(default=""),
    keyword: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    sql = """
        SELECT b.*, c.name AS category_name, c.type AS category_type
        FROM bills b JOIN categories c ON b.category_id = c.id
        WHERE b.user_id = ?
    """
    params: list = [user_id]
    if category_id:
        sql += " AND b.category_id = ?"
        params.append(category_id)
    if type in ("income", "expense"):
        sql += " AND c.type = ?"
        params.append(type)
    if month:
        sql += " AND substr(b.bill_date, 1, 7) = ?"
        params.append(month)
    if keyword:
        sql += " AND b.note LIKE ?"
        params.append(f"%{keyword}%")
    total = db.execute(
        f"SELECT COUNT(*) AS n FROM ({sql})", params
    ).fetchone()["n"]
    sql += " ORDER BY b.bill_date DESC, b.id DESC LIMIT ? OFFSET ?"
    rows = db.execute(sql, [*params, page_size, (page - 1) * page_size]).fetchall()
    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", status_code=201)
def create_bill(
    payload: BillPayload,
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    cat = _category_row(db, user_id, payload.category_id)
    amount = _validate_amount(payload.amount)
    month = payload.bill_date[:7]
    cur = db.execute(
        """
        INSERT INTO bills (user_id, category_id, amount, note, bill_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, cat["id"], amount, payload.note.strip(), payload.bill_date),
    )
    income = amount if cat["type"] == "income" else 0.0
    expense = amount if cat["type"] == "expense" else 0.0
    _upsert_summary(db, user_id, month, income, expense)
    db.commit()
    return {
        "id": cur.lastrowid,
        "category_id": cat["id"],
        "amount": amount,
        "note": payload.note.strip(),
        "bill_date": payload.bill_date,
    }


@router.put("/{bill_id}")
def update_bill(
    bill_id: int,
    payload: BillPayload,
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    old = db.execute(
        "SELECT * FROM bills WHERE id = ? AND user_id = ?", (bill_id, user_id)
    ).fetchone()
    if old is None:
        raise HTTPException(status_code=404, detail="账单不存在")
    new_cat = _category_row(db, user_id, payload.category_id)
    new_amount = _validate_amount(payload.amount)
    month = payload.bill_date[:7]

    db.execute(
        """
        UPDATE bills SET category_id = ?, amount = ?, note = ?, bill_date = ?
        WHERE id = ?
        """,
        (new_cat["id"], new_amount, payload.note.strip(), payload.bill_date, bill_id),
    )

    # 修正月度汇总：扣除旧值、累加新值
    old_cat = db.execute(
        "SELECT type FROM categories WHERE id = ?", (old["category_id"],)
    ).fetchone()
    old_income = old["amount"] if old_cat["type"] == "income" else 0.0
    old_expense = old["amount"] if old_cat["type"] == "expense" else 0.0
    if old["bill_date"][:7] != month:
        _upsert_summary(db, user_id, old["bill_date"][:7], -old_income, -old_expense)
    new_income = new_amount if new_cat["type"] == "income" else 0.0
    new_expense = new_amount if new_cat["type"] == "expense" else 0.0
    # 缺陷 D1：编辑金额后不刷新当月汇总（仍显示旧值）
    if not SEED_BUGS:
        _upsert_summary(
            db,
            user_id,
            month,
            new_income - (old_income if old["bill_date"][:7] == month else 0.0),
            new_expense - (old_expense if old["bill_date"][:7] == month else 0.0),
        )
    db.commit()
    return {
        "id": bill_id,
        "category_id": new_cat["id"],
        "amount": new_amount,
        "note": payload.note.strip(),
        "bill_date": payload.bill_date,
    }


@router.delete("/{bill_id}")
def delete_bill(
    bill_id: int,
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    old = db.execute(
        "SELECT * FROM bills WHERE id = ? AND user_id = ?", (bill_id, user_id)
    ).fetchone()
    if old is None:
        raise HTTPException(status_code=404, detail="账单不存在")
    cat = db.execute(
        "SELECT type FROM categories WHERE id = ?", (old["category_id"],)
    ).fetchone()
    income = old["amount"] if cat["type"] == "income" else 0.0
    expense = old["amount"] if cat["type"] == "expense" else 0.0
    _upsert_summary(db, user_id, old["bill_date"][:7], -income, -expense)
    db.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    db.commit()
    return {"ok": True}
