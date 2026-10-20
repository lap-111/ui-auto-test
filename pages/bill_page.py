"""账单页页面对象。"""
import re

from playwright.sync_api import expect

from base.base_page import BasePage


class BillPage(BasePage):
    def add_bill(self, category_label: str, amount: str, note: str = "") -> "BillPage":
        """新增一笔账单（按分类文案选择分类）。"""
        self.page.get_by_test_id("bill-category").select_option(label=category_label)
        self.fill("bill-amount", amount)
        self.fill("bill-note", note)
        self.click("bill-submit")
        return self

    def get_error(self) -> str:
        return self.text("bill-error")

    def bill_rows(self):
        return self.page.locator("[data-testid^='bill-row-']")

    def expect_row_count(self, count: int) -> "BillPage":
        expect(self.bill_rows()).to_have_count(count)
        return self

    def row_by_note(self, note: str):
        return self.bill_rows().filter(has_text=note)

    # ---- 筛选 ----
    def filter_by_month(self, month: str) -> "BillPage":
        self.page.get_by_test_id("bill-filter-month").fill(month)
        return self

    def filter_by_category(self, category_label: str) -> "BillPage":
        self.page.get_by_test_id("bill-filter-category").select_option(label=category_label)
        return self

    def search_keyword(self, keyword: str) -> "BillPage":
        self.fill("bill-filter-keyword", keyword)
        self.page.get_by_test_id("bill-filter-keyword").press("Enter")
        return self

    def reset_filter(self) -> "BillPage":
        self.click("bill-filter-reset")
        return self

    # ---- 编辑 / 删除 ----
    def edit_bill(self, bill_id: int, amount: str | None = None, note: str | None = None) -> "BillPage":
        self.refresh_list()
        self.page.get_by_test_id(f"bill-edit-{bill_id}").click()
        if amount is not None:
            self.fill("edit-amount", amount)
        if note is not None:
            self.fill("edit-note", note)
        self.click("edit-save")
        return self

    def get_edit_error(self) -> str:
        return self.text("edit-error")

    def delete_bill(self, bill_id: int, confirm: bool = True) -> "BillPage":
        self.refresh_list()
        self.page.get_by_test_id(f"bill-del-{bill_id}").click()
        self.page.get_by_test_id("confirm-modal").wait_for(state="visible")
        if confirm:
            self.click("confirm-ok")
        else:
            self.click("confirm-cancel")
        return self

    def refresh_list(self) -> "BillPage":
        """重置筛选并重新加载列表，确保包含测试阶段新建的数据。"""
        self.reset_filter()
        return self

    # ---- 分页 ----
    def goto_next_page(self) -> "BillPage":
        self.click("bill-page-next")
        return self

    def get_page_info(self) -> str:
        return self.text("bill-page-info")

    def amount_of_row(self, note: str) -> str:
        return self.row_by_note(note).locator(".amount").inner_text()
