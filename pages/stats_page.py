"""统计页页面对象。"""
from playwright.sync_api import expect

from base.base_page import BasePage


class StatsPage(BasePage):
    def open_tab(self, month: str | None = None) -> "StatsPage":
        self.click("tab-stats")
        if month is not None:
            self.page.get_by_test_id("stats-month").fill(month)
        self.click("stats-load")
        # 等待异步统计结果渲染完成（初始占位为 "-"）
        expect(self.page.get_by_test_id("stats-income")).not_to_have_text("-")
        return self

    def get_income(self) -> float:
        return self._parse(self.text("stats-income"))

    def get_expense(self) -> float:
        return self._parse(self.text("stats-expense"))

    def get_balance(self) -> float:
        return self._parse(self.text("stats-balance"))

    def category_total(self, name: str) -> float:
        row = self.page.locator("[data-testid^='stats-cat-']").filter(has_text=name)
        return self._parse(row.locator(".amount").inner_text())

    @staticmethod
    def _parse(value: str) -> float:
        return float(str(value).replace("+", "").replace("-", "").replace(",", ""))
