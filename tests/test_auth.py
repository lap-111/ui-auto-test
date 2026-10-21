"""用户模块用例。"""
import allure
import pytest
from playwright.sync_api import expect

from pages.login_page import LoginPage
from pages.register_page import RegisterPage
from utils.data_loader import load_yaml
from utils.random_data import random_username

AUTH_DATA = load_yaml("auth_data.yaml")
INVALID_LOGIN = AUTH_DATA["invalid_login"]
INVALID_REGISTER = AUTH_DATA["invalid_register"]


@allure.feature("用户模块")
@allure.story("登录")
@pytest.mark.smoke
@pytest.mark.p0
def test_login_success(admin_login):
    """正确账号密码登录成功，进入主界面并显示用户名。"""
    expect(admin_login.get_by_test_id("app-username")).to_have_text("admin")


@allure.feature("用户模块")
@allure.story("登录")
@pytest.mark.smoke
@pytest.mark.p0
def test_login_wrong_password(login_page):
    """错误密码登录，提示用户名或密码错误。"""
    login_page.login("admin", "wrong-password")
    expect(login_page.page.get_by_test_id("login-error")).to_have_text("用户名或密码错误")


@allure.feature("用户模块")
@allure.story("登录")
@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.parametrize("case", INVALID_LOGIN, ids=lambda c: c["password"] or "empty")
def test_login_invalid_parametrized(login_page, case):
    """数据驱动：非法登录场景均提示用户名或密码错误。"""
    login_page.login(case["username"], case["password"])
    expect(login_page.page.get_by_test_id("login-error")).to_have_text(case["error"])


@allure.feature("用户模块")
@allure.story("注册")
@pytest.mark.regression
def test_register_success(login_page):
    """注册新用户后自动登录进入主界面。"""
    username = random_username("reg")
    register = login_page.go_to_register()
    register.register(username, "abc123456")
    expect(login_page.page.get_by_test_id("app-username")).to_have_text(username)


@allure.feature("用户模块")
@allure.story("注册")
@pytest.mark.regression
@pytest.mark.parametrize(
    "case",
    INVALID_REGISTER,
    ids=lambda c: (c["username"] or "empty_user") + "-" + (c["password"] or "empty_pwd"),
)
def test_register_invalid(login_page, case):
    """数据驱动：非法注册场景给出对应提示。"""
    page = login_page.page
    page.get_by_test_id("login-to-register").click()
    RegisterPage(page).register(case["username"], case["password"])
    expect(page.get_by_test_id("register-error")).to_have_text(case["error"])


@allure.feature("用户模块")
@allure.story("登出")
@pytest.mark.regression
def test_logout(admin_login):
    """退出登录后回到登录页。"""
    admin_login.get_by_test_id("logout-btn").click()
    expect(admin_login.get_by_test_id("login-submit")).to_be_visible()


@allure.feature("用户模块")
@allure.story("修改密码")
@pytest.mark.regression
@pytest.mark.p1
def test_change_password_success(admin_login):
    """修改密码成功后需重新登录，新密码可正常登录。"""
    page = admin_login
    page.get_by_test_id("tab-settings").click()
    page.get_by_test_id("set-old").fill("123456")
    page.get_by_test_id("set-new").fill("newpass123")
    page.get_by_test_id("set-submit").click()
    expect(page.get_by_test_id("set-msg")).to_have_text("修改成功，请重新登录")
    expect(page.get_by_test_id("login-submit")).to_be_visible()
    LoginPage(page).login("admin", "newpass123")
    expect(page.get_by_test_id("app-username")).to_have_text("admin")


@allure.feature("用户模块")
@allure.story("修改密码")
@pytest.mark.regression
def test_change_password_wrong_old(admin_login):
    """原密码错误时修改失败。"""
    page = admin_login
    page.get_by_test_id("tab-settings").click()
    page.get_by_test_id("set-old").fill("wrong-old")
    page.get_by_test_id("set-new").fill("newpass123")
    page.get_by_test_id("set-submit").click()
    expect(page.get_by_test_id("set-msg")).to_have_text("原密码错误")


@allure.feature("用户模块")
@allure.story("修改密码")
@pytest.mark.regression
def test_change_password_empty_new(admin_login):
    """新密码为空时修改失败。"""
    page = admin_login
    page.get_by_test_id("tab-settings").click()
    page.get_by_test_id("set-old").fill("123456")
    page.get_by_test_id("set-submit").click()
    expect(page.get_by_test_id("set-msg")).to_have_text("新密码不能为空")


@allure.feature("用户模块")
@allure.story("登录")
@pytest.mark.regression
def test_index_requires_login(page, base_url):
    """未登录访问首页只展示登录卡片。"""
    page.goto(base_url + "/")
    expect(page.get_by_test_id("login-submit")).to_be_visible()
    expect(page.get_by_test_id("app-username")).to_have_count(0)