"""页面对象基类：封装 Playwright 通用操作与断言。"""
from playwright.sync_api import Page, expect


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    # ---- 基础操作 ----
    def fill(self, testid: str, value: str) -> "BasePage":
        self.page.get_by_test_id(testid).fill(value)
        return self

    def click(self, testid: str) -> "BasePage":
        self.page.get_by_test_id(testid).click()
        return self

    def text(self, testid: str) -> str:
        return self.page.get_by_test_id(testid).inner_text()

    # ---- 断言 ----
    def expect_visible(self, testid: str) -> "BasePage":
        expect(self.page.get_by_test_id(testid)).to_be_visible()
        return self

    def expect_text(self, testid: str, text: str) -> "BasePage":
        expect(self.page.get_by_test_id(testid)).to_have_text(text)
        return self
