"""pytest 全局 fixture：环境重置、接口客户端、页面对象。"""
import os

import pytest
import requests
from playwright.sync_api import Page

from api.client import ApiClient
from pages.login_page import LoginPage

BASE_URL = os.getenv("APP_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session", autouse=True)
def reset_env(base_url: str):
    """整个测试会话前后重置数据库，保证环境一致。"""
    requests.post(f"{base_url}/api/dev/reset", timeout=10).raise_for_status()
    yield
    requests.post(f"{base_url}/api/dev/reset", timeout=10).raise_for_status()


@pytest.fixture(scope="session")
def api(base_url: str) -> ApiClient:
    return ApiClient(base_url)


@pytest.fixture
def admin_token(api: ApiClient) -> str:
    r = api.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture
def admin_api(admin_token: str, base_url: str) -> ApiClient:
    return ApiClient(base_url, admin_token)


@pytest.fixture
def login_page(page: Page, base_url: str) -> LoginPage:
    """打开登录页。"""
    return LoginPage(page).open(base_url)


@pytest.fixture
def admin_login(page: Page, base_url: str) -> Page:
    """以种子账号登录后返回页面。"""
    LoginPage(page).open(base_url).login("admin", "123456")
    return page
