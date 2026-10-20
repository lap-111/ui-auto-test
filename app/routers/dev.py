"""开发/测试专用路由：重置环境、特性开关。"""
from fastapi import APIRouter

from ..config import SEED_BUGS
from ..seed import reset_and_seed

router = APIRouter()


@router.post("/reset")
def reset_env():
    """清空数据库并写入种子数据（测试前置造数使用）。"""
    reset_and_seed()
    return {"ok": True}


@router.get("/features")
def features():
    """测试特性开关（缺陷注入状态），供前端/测试控制渲染路径。"""
    return {"xss": SEED_BUGS}
