"""账单页页面对象。"""
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
