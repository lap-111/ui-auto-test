"""登录页页面对象。"""
from base.base_page import BasePage
from pages.register_page import RegisterPage


class LoginPage(BasePage):
    def open(self, base_url: str) -> "LoginPage":
        self.page.goto(f"{base_url}/")
        return self

    def login(self, username: str, password: str) -> "LoginPage":
        self.fill("login-username", username).fill("login-password", password)
        self.click("login-submit")
        return self

    def get_error(self) -> str:
        return self.text("login-error")

    def go_to_register(self) -> "RegisterPage":
        self.click("login-to-register")
        return RegisterPage(self.page)
