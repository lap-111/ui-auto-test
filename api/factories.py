"""接口造数工厂：通过被测应用 API 快速准备/清理数据。"""
import datetime

from api.client import ApiClient


def create_category(api: ApiClient, name: str, type: str = "expense") -> dict:
    r = api.post("/api/categories", json={"name": name, "type": type})
    r.raise_for_status()
    return r.json()


def list_categories(api: ApiClient, type: str = "") -> list:
    path = "/api/categories" + (f"?type={type}" if type else "")
    r = api.get(path)
    r.raise_for_status()
    return r.json()


def create_bill(
    api: ApiClient,
    category_id: int,
    amount: float,
    note: str = "",
    bill_date: str | None = None,
) -> dict:
    payload = {
        "category_id": category_id,
        "amount": amount,
        "note": note,
        "bill_date": bill_date or datetime.date.today().isoformat(),
    }
    r = api.post("/api/bills", json=payload)
    r.raise_for_status()
    return r.json()


def list_bills(api: ApiClient, **params) -> dict:
    r = api.get("/api/bills", params=params)
    r.raise_for_status()
    return r.json()


def delete_bill(api: ApiClient, bill_id: int) -> None:
    api.delete(f"/api/bills/{bill_id}").raise_for_status()


def monthly_stats(api: ApiClient, month: str | None = None) -> dict:
    path = "/api/stats/monthly" + (f"?month={month}" if month else "")
    r = api.get(path)
    r.raise_for_status()
    return r.json()
