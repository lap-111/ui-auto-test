"""种子数据：初始化演示账号、分类、账单。"""
import datetime
import sqlite3

from .db import DB_PATH, reset_db
from .security import hash_password

DB_OWNER = "admin"
DB_PASSWORD = "123456"

SEED_CATEGORIES = [
    ("餐饮", "expense"),
    ("交通", "expense"),
    ("购物", "expense"),
    ("工资", "income"),
    ("奖金", "income"),
]


def _today() -> str:
    return datetime.date.today().strftime("%Y-%m-%d")


def _last_month_today() -> str:
    today = datetime.date.today()
    first = today.replace(day=1)
    last = first - datetime.timedelta(days=1)
    return last.strftime("%Y-%m-%d")


def seed(conn: sqlite3.Connection) -> None:
    """写入演示数据，并保证月度汇总与账单一致。"""
    cur = conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (DB_OWNER, hash_password(DB_PASSWORD)),
    )
    owner_id = cur.lastrowid

    cat_ids = {}
    for name, ctype in SEED_CATEGORIES:
        c = conn.execute(
            "INSERT INTO categories (user_id, name, type) VALUES (?, ?, ?)",
            (owner_id, name, ctype),
        )
        cat_ids[name] = c.lastrowid

    today = _today()
    last = _last_month_today()

    bills = [
        (cat_ids["餐饮"], 35.50, "午餐", today),
        (cat_ids["交通"], 12.00, "地铁", today),
        (cat_ids["购物"], 199.00, "日用品", today),
        (cat_ids["工资"], 15000.00, "6月工资", today),
        (cat_ids["餐饮"], 88.00, "晚餐聚餐", last),
        (cat_ids["奖金"], 2000.00, "项目奖金", last),
    ]
    for cat_id, amount, note, bill_date in bills:
        conn.execute(
            "INSERT INTO bills (user_id, category_id, amount, note, bill_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (owner_id, cat_id, amount, note, bill_date),
        )

    # 按账单实时汇总写入 monthly_summary
    for row in conn.execute(
        """
        SELECT substr(b.bill_date, 1, 7) AS month, c.type, SUM(b.amount) AS total
        FROM bills b JOIN categories c ON b.category_id = c.id
        WHERE b.user_id = ?
        GROUP BY month, c.type
        """,
        (owner_id,),
    ):
        conn.execute(
            """
            INSERT INTO monthly_summary (user_id, month, income, expense)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, month) DO UPDATE SET
                income = income + excluded.income,
                expense = expense + excluded.expense
            """,
            (
                owner_id,
                row["month"],
                row["total"] if row["type"] == "income" else 0,
                row["total"] if row["type"] == "expense" else 0,
            ),
        )
    conn.commit()


def reset_and_seed() -> None:
    """重置数据库并写入种子数据（供 /api/dev/reset 与测试前置使用）。"""
    reset_db()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        seed(conn)
    finally:
        conn.close()
