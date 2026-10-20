"""API 客户端：封装测试前置造数与数据清理请求。"""
import requests


class ApiClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers["X-Token"] = token

    def get(self, path: str, **kwargs):
        return self.session.get(self.base_url + path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.session.post(self.base_url + path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.session.put(self.base_url + path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.session.delete(self.base_url + path, **kwargs)

    def reset(self) -> None:
        """重置数据库并写入种子数据。"""
        self.post("/api/dev/reset", timeout=10).raise_for_status()
