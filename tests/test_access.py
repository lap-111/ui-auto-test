"""接口与访问控制用例。"""
import allure
import pytest
import requests


@allure.feature("接口与权限")
@allure.story("鉴权")
@pytest.mark.regression
def test_api_requires_token(base_url):
    """未携带 token 访问业务接口返回 401。"""
    r = requests.get(f"{base_url}/api/bills", timeout=10)
    assert r.status_code == 401


@allure.feature("接口与权限")
@allure.story("环境重置")
@pytest.mark.regression
def test_api_reset_env(base_url):
    """重置接口可用，返回 ok。"""
    r = requests.post(f"{base_url}/api/dev/reset", timeout=10)
    assert r.status_code == 200
    assert r.json() == {"ok": True}


@allure.feature("接口与权限")
@allure.story("鉴权")
@pytest.mark.regression
def test_api_register_login_flow(base_url):
    """注册新用户后可用新账号登录。"""
    from utils.random_data import random_username

    username = random_username("api")
    r = requests.post(
        f"{base_url}/api/auth/register",
        json={"username": username, "password": "abc123456"},
        timeout=10,
    )
    assert r.status_code == 201
    r = requests.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": "abc123456"},
        timeout=10,
    )
    assert r.status_code == 200
    assert "token" in r.json()