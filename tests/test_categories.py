"""分类模块用例。"""
import pytest
from playwright.sync_api import expect

from api import factories as f
from pages.category_page import CategoryPage


@pytest.mark.regression
def test_seed_categories_count(admin_login):
    """种子数据包含 5 个分类。"""
    cat = CategoryPage(admin_login)
    cat.open_tab()
    cat.expect_row_count(5)


@pytest.mark.regression
def test_add_expense_category(admin_login):
    """新增支出分类并展示。"""
    cat = CategoryPage(admin_login)
    cat.open_tab().add_category("健身")
    expect(cat.row_by_name("健身")).to_contain_text("支出")
    cat.expect_row_count(6)


@pytest.mark.regression
def test_add_income_category(admin_login):
    """新增收入分类并展示。"""
    cat = CategoryPage(admin_login)
    cat.open_tab().add_category("理财", "income")
    expect(cat.row_by_name("理财")).to_contain_text("收入")


@pytest.mark.regression
@pytest.mark.p1
def test_add_duplicate_category(admin_login):
    """分类重名给出明确提示（缺陷 D3 捕获点）。"""
    cat = CategoryPage(admin_login)
    cat.open_tab().add_category("餐饮")
    expect(cat.page.get_by_test_id("cat-error")).to_have_text("分类名称已存在")


@pytest.mark.regression
def test_add_empty_category(admin_login):
    """分类名称为空给出提示。"""
    cat = CategoryPage(admin_login)
    cat.open_tab().add_category("")
    expect(cat.page.get_by_test_id("cat-error")).to_have_text("分类名称不能为空")


@pytest.mark.regression
def test_delete_category_without_bills(admin_login):
    """无账单引用的分类可删除。"""
    cat = CategoryPage(admin_login)
    cat.open_tab().add_category("待删分类")
    cat.expect_row_count(6)
    cat.delete_by_name("待删分类")
    cat.expect_row_count(5)


@pytest.mark.regression
def test_delete_category_with_bills_fails(admin_api, admin_login):
    """存在账单引用的分类不可删除并给出提示。"""
    cat_data = f.create_category(admin_api, "有账单分类")
    f.create_bill(admin_api, cat_data["id"], 10, note="关联账单")
    cat = CategoryPage(admin_login)
    cat.open_tab()
    cat.delete_by_name("有账单分类")
    expect(cat.page.get_by_test_id("cat-error")).to_have_text("该分类下存在账单，无法删除")
    cat.expect_row_count(6)


@pytest.mark.regression
def test_new_category_in_bill_dropdown(admin_login):
    """新增分类后出现在记账表单下拉中。"""
    cat = CategoryPage(admin_login)
    cat.open_tab().add_category("旅行")
    cat.click("tab-bills")
    options = cat.page.get_by_test_id("bill-category").locator("option").all_inner_texts()
    assert any("旅行" in o for o in options)


@pytest.mark.regression
def test_delete_category_removes_from_dropdown(admin_api, admin_login):
    """删除分类后从记账表单下拉中消失。"""
    cat_data = f.create_category(admin_api, "临时分类")
    cat = CategoryPage(admin_login)
    cat.open_tab().delete_by_name("临时分类")
    cat.click("tab-bills")
    options = cat.page.get_by_test_id("bill-category").locator("option").all_inner_texts()
    assert not any("临时分类" in o for o in options)
