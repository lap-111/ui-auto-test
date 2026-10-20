"""随机测试数据工厂：生成用例间不冲突的独立数据。"""
import datetime
import random
import string


def random_username(prefix: str = "user") -> str:
    """生成随机用户名，避免用例间重复冲突。"""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suffix}"


def random_amount(min_value: float = 1.0, max_value: float = 1000.0) -> float:
    """生成两位小数的随机金额。"""
    return round(random.uniform(min_value, max_value), 2)


def today() -> str:
    return datetime.date.today().isoformat()


def this_month() -> str:
    return datetime.date.today().strftime("%Y-%m")


def last_month() -> str:
    today = datetime.date.today()
    first = today.replace(day=1)
    return (first - datetime.timedelta(days=1)).strftime("%Y-%m")


def date_in_month(month: str, day: int = 15) -> str:
    return f"{month}-{day:02d}"
