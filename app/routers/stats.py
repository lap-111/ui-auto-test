"""报表模块路由：月度收支统计。"""
import sqlite3

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..db import get_db
from ..deps import require_user

router = APIRouter()


class _CategoryStat(BaseModel):
    category_id: int
    name: str
    type: str
    total: float


@router.get("/monthly")
def monthly_stats(
    month: str = Query(default=""),
    user_id: int = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    import datetime

    month = month or datetime.date.today().strftime("%Y-%m")
    summary = db.execute(
        "SELECT income, expense FROM monthly_summary WHERE user_id = ? AND month = ?",
        (user_id, month),
    ).fetchone()

    # 兜底：汇总缺失时按账单实时计算并补齐
    if summary is None:
        income, expense = 0.0, 0.0
        for row in db.execute(
            """
            SELECT c.type, b.amount FROM bills b
            JOIN categories c ON b.category_id = c.id
            WHERE b.user_id = ? AND substr(b.bill_date, 1, 7) = ?
            """,
            (user_id, month),
        ):
            if row["type"] == "income":
                income += row["amount"]
            else:
                expense += row["amount"]
        db.execute(
            """
            INSERT INTO monthly_summary (user_id, month, income, expense)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, month, income, expense),
        )
        db.commit()
        summary = {"income": income, "expense": expense}

    by_category = []
    for row in db.execute(
        """
        SELECT c.id AS category_id, c.name, c.type, SUM(b.amount) AS total
        FROM bills b JOIN categories c ON b.category_id = c.id
        WHERE b.user_id = ? AND substr(b.bill_date, 1, 7) = ?
        GROUP BY c.id
        """,
        (user_id, month),
    ):
        by_category.append(
            _CategoryStat(
                category_id=row["category_id"],
                name=row["name"],
                type=row["type"],
                total=row["total"],
            ).model_dump()
        )

    return {
        "month": month,
        "income": round(summary["income"], 2),
        "expense": round(summary["expense"], 2),
        "balance": round(summary["income"] - summary["expense"], 2),
        "by_category": by_category,
    }
