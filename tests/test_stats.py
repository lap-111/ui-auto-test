"""报表模块用例。"""
import pytest

from api import factories as f
from pages.bill_page import BillPage
from pages.stats_page import StatsPage
from utils.random_data import last_month, this_month

SEED_EXPENSE = 35.5 + 12 + 199  # 246.5
SEED_INCOME = 15000.0
SEED_BALANCE = SEED_INCOME - SEED_EXPENSE


@pytest.mark.regression
@pytest.mark.p0
def test_stats_current_month(admin_login):
    """当月统计与种子数据一致。"""
    stats = StatsPage(admin_login)
    stats.open_tab(this_month())
    assert stats.get_income() == pytest.approx(SEED_INCOME, abs=0.01)
    assert stats.get_expense() == pytest.approx(SEED_EXPENSE, abs=0.01)
    assert stats.get_balance() == pytest.approx(SEED_BALANCE, abs=0.01)


@pytest.mark.regression
def test_stats_last_month(admin_login):
    """切换上月统计正确。"""
    stats = StatsPage(admin_login)
    stats.open_tab(last_month())
    assert stats.get_income() == pytest.approx(2000.0, abs=0.01)
    assert stats.get_expense() == pytest.approx(88.0, abs=0.01)


@pytest.mark.regression
def test_stats_empty_month(admin_login):
    """无数据月份统计为 0。"""
    stats = StatsPage(admin_login)
    stats.open_tab("2099-12")
    assert stats.get_income() == 0
    assert stats.get_expense() == 0
    assert stats.get_balance() == 0


@pytest.mark.regression
def test_stats_category_breakdown(admin_login):
    """分类汇总金额正确。"""
    stats = StatsPage(admin_login)
    stats.open_tab(this_month())
    assert stats.category_total("餐饮") == pytest.approx(35.5, abs=0.01)
    assert stats.category_total("工资") == pytest.approx(15000.0, abs=0.01)


@pytest.mark.regression
@pytest.mark.p1
def test_add_bill_reflects_in_stats(admin_api, admin_login):
    """新增账单后页面统计同步（UI 联动）。"""
    cm = this_month()
    before = f.monthly_stats(admin_api, cm)
    BillPage(admin_login).add_bill("购物（支出）", "55.00", "统计联动")
    stats = StatsPage(admin_login)
    stats.open_tab(cm)
    assert stats.get_expense() == pytest.approx(before["expense"] + 55.0, abs=0.01)


@pytest.mark.regression
@pytest.mark.p1
def test_edit_bill_reflects_in_stats(admin_api, admin_login):
    """编辑账单金额后页面统计同步（缺陷 D1 捕获点）。"""
    cm = this_month()
    exp_cat = f.list_categories(admin_api, type="expense")[0]
    created = f.create_bill(admin_api, exp_cat["id"], 100, note="编辑统计")
    BillPage(admin_login).edit_bill(created["id"], amount="400")
    stats = StatsPage(admin_login)
    stats.open_tab(cm)
    # 种子支出 246.5 + 新增 100，编辑 100→400 再 +300
    assert stats.get_expense() == pytest.approx(SEED_EXPENSE + 100 + 300, abs=0.01)
