"""应用配置：通过环境变量控制。"""
import os

# 是否注入隐藏缺陷（用于演示测试用例捕获 Bug 的能力）
SEED_BUGS = os.getenv("SEED_BUGS", "0") == "1"

# 应用监听端口
APP_PORT = int(os.getenv("APP_PORT", "8000"))
