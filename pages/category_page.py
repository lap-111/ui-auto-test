"""分类页页面对象。"""
import re

from playwright.sync_api import expect

from base.base_page import BasePage


class CategoryPage(BasePage):
    def open_tab(self) -> "CategoryPage":
        self.click("tab-categories")
        return self

    def add_category(self, name: str, type: str = "expense") -> "CategoryPage":
        self.fill("cat-name", name)
        self.page.get_by_test_id("cat-type").select_option(type)
        self.click("cat-submit")
        return self

    def get_error(self) -> str:
        return self.text("cat-error")

    def cat_rows(self):
        return self.page.locator("[data-testid^='cat-row-']")

    def row_by_name(self, name: str):
        return self.cat_rows().filter(has_text=name)

    def expect_row_count(self, count: int) -> "CategoryPage":
        expect(self.cat_rows()).to_have_count(count)
        return self

    def delete_by_name(self, name: str) -> "CategoryPage":
        """删除指定名称的分类（通过自定义确认弹窗）。"""
        row = self.row_by_name(name)
        row.get_by_test_id(re.compile(r"cat-del-\d+")).click()
        self.page.get_by_test_id("confirm-modal").wait_for(state="visible")
        self.click("confirm-ok")
        return self
