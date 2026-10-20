"""pytest 全局 fixture：环境重置、接口客户端、页面对象。"""
import os

import pytest
from playwright.sync_api import Page

from api.client import ApiClient
from pages.login_page import LoginPage

BASE_URL = os.getenv("APP_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def api(base_url: str) -> ApiClient:
    return ApiClient(base_url)


@pytest.fixture
def reset_env(api: ApiClient):
    """每个用例执行前重置数据库并写入种子数据，保证用例间完全隔离。"""
    api.reset()
    yield


@pytest.fixture(autouse=True)
def _reset_before_each(reset_env):
    yield


@pytest.fixture
def admin_token(reset_env, api: ApiClient) -> str:
    r = api.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture
def admin_api(admin_token: str, base_url: str) -> ApiClient:
    return ApiClient(base_url, admin_token)


@pytest.fixture
def login_page(reset_env, page: Page, base_url: str) -> LoginPage:
    """打开登录页。"""
    return LoginPage(page).open(base_url)


@pytest.fixture
def admin_login(reset_env, page: Page, base_url: str) -> Page:
    """以种子账号登录后返回页面。"""
    LoginPage(page).open(base_url).login("admin", "123456")
    return page


def pytest_runtest_makereport(item, call):
    """失败时附加全页截图到 Allure 报告。"""
    if call.when == "call" and call.excinfo is not None:
        page = item.funcargs.get("page")
        if page is not None:
            try:
                import allure

                shot = page.screenshot(full_page=True)
                allure.attach(
                    shot,
                    name="失败截图",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception:
                # 截图失败不影响用例结果
                pass
