"""记账模块冒烟用例。"""
import pytest
from playwright.sync_api import expect

from pages.bill_page import BillPage


@pytest.mark.smoke
@pytest.mark.p0
def test_add_bill_smoke(admin_login):
    """新增一笔支出账单，列表首行展示金额与备注。"""
    bill_page = BillPage(admin_login)
    bill_page.add_bill("餐饮（支出）", "66.60", "冒烟测试")
    expect(bill_page.bill_rows().first).to_contain_text("66.60")
    expect(bill_page.bill_rows().first).to_contain_text("冒烟测试")
