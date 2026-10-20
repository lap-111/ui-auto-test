"""用户模块冒烟用例。"""
import pytest
from playwright.sync_api import expect


@pytest.mark.smoke
@pytest.mark.p0
def test_login_success(admin_login):
    """正确账号密码登录成功，进入主界面并显示用户名。"""
    expect(admin_login.get_by_test_id("app-username")).to_have_text("admin")


@pytest.mark.smoke
@pytest.mark.p0
def test_login_wrong_password(login_page):
    """错误密码登录，提示用户名或密码错误。"""
    login_page.login("admin", "wrong-password")
    expect(login_page.page.get_by_test_id("login-error")).to_have_text("用户名或密码错误")
