"""开发/测试专用路由：重置环境。"""
from fastapi import APIRouter

from ..seed import reset_and_seed

router = APIRouter()


@router.post("/reset")
def reset_env():
    """清空数据库并写入种子数据（测试前置造数使用）。"""
    reset_and_seed()
    return {"ok": True}
