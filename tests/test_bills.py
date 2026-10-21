"""记账模块用例。"""
import allure
import pytest
from playwright.sync_api import expect

from api import factories as f
from pages.bill_page import BillPage
from utils.data_loader import load_yaml
from utils.random_data import date_in_month, last_month, this_month

BILL_DATA = load_yaml("bill_data.yaml")
INVALID_AMOUNTS = BILL_DATA["invalid_amount"]
SPECIAL_NOTES = BILL_DATA["special_notes"]


def cat_label(name: str, type: str = "expense") -> str:
    return f"{name}（{'收入' if type == 'income' else '支出'}）"


@allure.feature("记账模块")
@allure.story("新增")
@pytest.mark.smoke
@pytest.mark.p0
def test_add_bill_smoke(admin_login):
    """新增一笔支出账单，列表首行展示金额与备注。"""
    bill = BillPage(admin_login)
    bill.add_bill("餐饮（支出）", "66.60", "冒烟测试")
    expect(bill.bill_rows().first).to_contain_text("66.60")
    expect(bill.bill_rows().first).to_contain_text("冒烟测试")


@allure.feature("记账模块")
@allure.story("新增")
@pytest.mark.regression
@pytest.mark.parametrize("case", INVALID_AMOUNTS, ids=lambda c: f"amount_{c['amount']}")
def test_add_bill_invalid_amount(admin_login, case):
    """数据驱动：非法金额被前端校验拦截。"""
    bill = BillPage(admin_login)
    bill.add_bill("餐饮（支出）", case["amount"], "")
    expect(bill.page.get_by_test_id("bill-error")).to_have_text(case["error"])


@allure.feature("记账模块")
@allure.story("新增")
@pytest.mark.regression
def test_add_bill_without_category(admin_login):
    """未选择分类时被前端校验拦截。"""
    bill = BillPage(admin_login)
    bill.fill("bill-amount", "10").click("bill-submit")
    expect(bill.page.get_by_test_id("bill-error")).to_have_text("请选择分类")


@allure.feature("记账模块")
@allure.story("新增")
@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.parametrize("note", SPECIAL_NOTES, ids=lambda n: n[:12])
def test_add_bill_special_note(admin_login, note):
    """特殊字符备注应原样展示，且不破坏页面（缺陷 D2 捕获点）。"""
    bill = BillPage(admin_login)
    bill.add_bill("餐饮（支出）", "10.50", note)
    expect(bill.page).to_have_title("MoneyKeeper 记账本")
    expect(bill.row_by_note(note).first).to_be_visible()


@allure.feature("记账模块")
@allure.story("新增")
@pytest.mark.regression
def test_add_income_bill_shows_plus(admin_login):
    """新增收入账单以 + 号展示。"""
    bill = BillPage(admin_login)
    bill.add_bill("工资（收入）", "8888.00", "收入测试")
    expect(bill.bill_rows().first).to_contain_text("+8888.00")


@allure.feature("记账模块")
@allure.story("新增")
@pytest.mark.regression
def test_amount_precision(admin_login):
    """金额最小精度 0.01 正常展示。"""
    bill = BillPage(admin_login)
    bill.add_bill("餐饮（支出）", "0.01", "一分钱")
    expect(bill.bill_rows().first).to_contain_text("0.01")


@allure.feature("记账模块")
@allure.story("列表")
@pytest.mark.regression
def test_default_list_shows_seed_bills(admin_login):
    """默认列表展示种子数据全部账单。"""
    bill = BillPage(admin_login)
    bill.expect_row_count(6)


@allure.feature("记账模块")
@allure.story("编辑")
@pytest.mark.regression
def test_edit_bill_amount(admin_api, admin_login):
    """编辑账单金额后，列表展示新金额。"""
    cid = f.list_categories(admin_api, type="expense")[0]["id"]
    created = f.create_bill(admin_api, cid, 100.00, note="待改金额")
    bill = BillPage(admin_login)
    bill.edit_bill(created["id"], amount="200.00")
    expect(bill.row_by_note("待改金额")).to_contain_text("200.00")


@allure.feature("记账模块")
@allure.story("编辑")
@pytest.mark.regression
def test_edit_bill_note(admin_api, admin_login):
    """编辑账单备注后，列表展示新备注。"""
    cid = f.list_categories(admin_api, type="expense")[0]["id"]
    created = f.create_bill(admin_api, cid, 30.00, note="旧备注")
    bill = BillPage(admin_login)
    bill.edit_bill(created["id"], note="新备注")
    expect(bill.row_by_note("新备注")).to_be_visible()
    expect(bill.row_by_note("旧备注")).to_have_count(0)


@allure.feature("记账模块")
@allure.story("编辑")
@pytest.mark.regression
def test_edit_bill_invalid_amount(admin_api, admin_login):
    """编辑时输入非法金额被拦截。"""
    cid = f.list_categories(admin_api, type="expense")[0]["id"]
    created = f.create_bill(admin_api, cid, 30.00, note="编辑非法")
    bill = BillPage(admin_login)
    bill.page.get_by_test_id(f"bill-edit-{created['id']}").click()
    bill.fill("edit-amount", "0")
    bill.click("edit-save")
    expect(bill.page.get_by_test_id("edit-error")).to_have_text("金额必须大于 0")


@allure.feature("记账模块")
@allure.story("删除")
@pytest.mark.regression
def test_delete_bill(admin_api, admin_login):
    """删除账单后列表数量减少。"""
    cid = f.list_categories(admin_api, type="expense")[0]["id"]
    created = f.create_bill(admin_api, cid, 10.00, note="待删除")
    bill = BillPage(admin_login)
    bill.expect_row_count(7)
    bill.delete_bill(created["id"])
    bill.expect_row_count(6)
    expect(bill.row_by_note("待删除")).to_have_count(0)


@allure.feature("记账模块")
@allure.story("删除")
@pytest.mark.regression
def test_delete_bill_cancel(admin_api, admin_login):
    """删除弹窗取消后账单保留。"""
    cid = f.list_categories(admin_api, type="expense")[0]["id"]
    created = f.create_bill(admin_api, cid, 10.00, note="保留账单")
    bill = BillPage(admin_login)
    bill.delete_bill(created["id"], confirm=False)
    bill.expect_row_count(7)
    expect(bill.row_by_note("保留账单")).to_be_visible()


@allure.feature("记账模块")
@allure.story("筛选")
@pytest.mark.regression
def test_filter_by_month(admin_api, admin_login):
    """按月筛选账单。"""
    lm, cm = last_month(), this_month()
    cid = f.list_categories(admin_api, type="expense")[0]["id"]
    f.create_bill(admin_api, cid, 10, note="上月账单", bill_date=date_in_month(lm))
    f.create_bill(admin_api, cid, 20, note="本月账单")
    bill = BillPage(admin_login)
    bill.filter_by_month(lm)
    expect(bill.row_by_note("上月账单")).to_be_visible()
    expect(bill.row_by_note("本月账单")).to_have_count(0)
    bill.filter_by_month(cm)
    expect(bill.row_by_note("本月账单")).to_be_visible()
    expect(bill.row_by_note("上月账单")).to_have_count(0)


@allure.feature("记账模块")
@allure.story("筛选")
@pytest.mark.regression
def test_filter_by_category(admin_api, admin_login):
    """按分类筛选账单。"""
    income_cat = f.list_categories(admin_api, type="income")[0]
    exp_cat = f.list_categories(admin_api, type="expense")[0]
    f.create_bill(admin_api, income_cat["id"], 5000, note="工资单")
    f.create_bill(admin_api, exp_cat["id"], 30, note="外卖")
    bill = BillPage(admin_login)
    bill.filter_by_category(cat_label(income_cat["name"], "income"))
    expect(bill.row_by_note("工资单")).to_be_visible()
    expect(bill.row_by_note("外卖")).to_have_count(0)


@allure.feature("记账模块")
@allure.story("筛选")
@pytest.mark.regression
def test_search_keyword(admin_api, admin_login):
    """按备注关键字搜索。"""
    cid = f.list_categories(admin_api, type="expense")[0]["id"]
    f.create_bill(admin_api, cid, 5, note="买咖啡")
    f.create_bill(admin_api, cid, 8, note="买奶茶")
    bill = BillPage(admin_login)
    bill.search_keyword("咖啡")
    expect(bill.row_by_note("买咖啡")).to_be_visible()
    expect(bill.row_by_note("买奶茶")).to_have_count(0)


@allure.feature("记账模块")
@allure.story("分页")
@pytest.mark.regression
def test_pagination(admin_api, admin_login):
    """超过一页时自动分页，可翻页。"""
    cid = f.list_categories(admin_api, type="expense")[0]["id"]
    for i in range(12):
        f.create_bill(admin_api, cid, 1, note=f"分页账单{i:02d}")
    bill = BillPage(admin_login)
    bill.reset_filter()
    bill.expect_row_count(10)
    assert "第 1/2 页" in bill.get_page_info()
    bill.goto_next_page()
    bill.expect_row_count(8)
    assert "第 2/2 页" in bill.get_page_info()


@allure.feature("记账模块")
@allure.story("筛选")
@pytest.mark.regression
def test_bill_future_month(admin_api, admin_login):
    """未来月份账单可通过月份筛选查看。"""
    cid = f.list_categories(admin_api, type="expense")[0]["id"]
    f.create_bill(admin_api, cid, 15, note="未来账单", bill_date="2099-01-01")
    bill = BillPage(admin_login)
    bill.filter_by_month("2099-01")
    expect(bill.row_by_note("未来账单")).to_be_visible()


@allure.feature("记账模块")
@allure.story("联动验证")
@pytest.mark.regression
@pytest.mark.p1
def test_add_bill_updates_stats(admin_api, admin_login):
    """新增账单后，月度统计支出同步增加。"""
    cm = this_month()
    before = f.monthly_stats(admin_api, cm)
    BillPage(admin_login).add_bill("餐饮（支出）", "66.60", "联动统计")
    after = f.monthly_stats(admin_api, cm)
    assert after["expense"] == pytest.approx(before["expense"] + 66.6, abs=0.01)


@allure.feature("记账模块")
@allure.story("联动验证")
@pytest.mark.regression
@pytest.mark.p1
def test_edit_bill_updates_stats(admin_api, admin_login):
    """编辑账单金额后，月度统计支出同步（缺陷 D1 捕获点）。"""
    cm = this_month()
    exp_cat = f.list_categories(admin_api, type="expense")[0]
    created = f.create_bill(admin_api, exp_cat["id"], 100, note="编辑联动")
    before = f.monthly_stats(admin_api, cm)
    BillPage(admin_login).edit_bill(created["id"], amount="300")
    after = f.monthly_stats(admin_api, cm)
    assert after["expense"] == pytest.approx(before["expense"] + 200, abs=0.01)