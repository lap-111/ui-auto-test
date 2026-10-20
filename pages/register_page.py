"""注册页页面对象。"""
from base.base_page import BasePage


class RegisterPage(BasePage):
    def register(self, username: str, password: str) -> "RegisterPage":
        self.fill("register-username", username).fill("register-password", password)
        self.click("register-submit")
        return self

    def get_error(self) -> str:
        return self.text("register-error")
