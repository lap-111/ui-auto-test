# MoneyKeeper UI 自动化测试平台

一个学习「测试开发」的完整个人项目：**自研记账 Web 应用 + Playwright 自动化回归框架**，形成「被测应用 → 自动化框架 → 测试报告 → CI 持续回归」的完整闭环。

- 被测对象：自研 FastAPI 记账应用（SQLite + 原生前端）
- 测试框架：Playwright + Pytest + POM 页面对象模式 + YAML 数据驱动
- 报告与 CI：Allure 报告 + GitHub Actions 每日全量回归

## 项目亮点

- **被测对象可控**：自研应用可任意造数、重置环境、注入隐藏缺陷
- **能发现真缺陷**：预置 3 个隐藏 Bug，测试用例可真实捕获（详见「缺陷捕获演示」）
- **完整工程化**：POM 分层、数据驱动、失败截图/录屏、用例隔离、CI 哑回归、Allure 报告

## 技术栈

| 领域 | 选型 |
|---|---|
| 被测应用 | Python 3.11 · FastAPI · SQLite · 原生 HTML/JS |
| 测试框架 | Playwright 1.50 · Pytest 8.3 |
| 数据驱动 | YAML + pytest.parametrize |
| 报告 | Allure 2 · 失败自动截图 + trace 录屏 |
| CI | GitHub Actions（push/PR 回归 + cron 每日全量） |

## 目录结构

```
ui_auto_test/
├── app/                      # 被测应用（FastAPI 记账本）
│   ├── main.py               # 应用入口
│   ├── db.py                 # SQLite 数据层
│   ├── routers/              # auth / bills / categories / stats / dev
│   ├── seed.py               # 种子数据 + 缺陷注入
│   └── static/               # 前端页面（HTML/JS/CSS）
├── tests/                    # 用例层：只写「步骤 + 断言」
│   ├── conftest.py           # fixture：重置环境 / 登录 / 页面对象
│   ├── test_auth.py          # 用户模块（13 用例）
│   ├── test_bills.py         # 记账模块（22 用例）
│   ├── test_categories.py    # 分类模块（9 用例）
│   ├── test_stats.py         # 报表模块（6 用例）
│   └── test_access.py        # 接口与访问控制（3 用例）
├── pages/                    # 页面对象层：一页一类（POM）
├── base/                     # 基础层：BasePage 通用封装
├── api/                      # 接口层：前置造数 / 数据清理
├── data/                     # YAML 数据驱动文件
├── utils/                    # 随机数据工厂 / YAML 加载
├── pytest.ini                # 标记 smoke/regression/p0/p1
├── requirements-dev.txt
├── .github/workflows/ui-test.yml
└── docs/project_design.md    # 项目设计文档
```

## 快速开始

### 1. 环境准备（Python 3.11 + venv）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1           # cmd: .venv\Scripts\activate.bat
pip install -r requirements-dev.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m playwright install chromium  # 安装浏览器
```

### 2. 启动被测应用

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

> 默认账号：`admin / 123456`（种子数据自动初始化）

### 3. 运行测试

```powershell
.\.venv\Scripts\python -m pytest                 # 全部 54 用例
.\.venv\Scripts\python -m pytest -m smoke        # 仅冒烟
.\.venv\Scripts\python -m pytest -m p1           # 仅 P1 级
```

### 4. 生成 Allure 报告

```powershell
allure generate allure-results -o allure-report --clean
python -m http.server 8082 --directory allure-report   # 打开 http://127.0.0.1:8082
```

> `allure` 命令行通过 `npm i -g allure-commandline` 安装。

## 缺陷捕获演示

应用通过环境变量 `SEED_BUGS=1` 注入 3 个隐藏缺陷，用于演示「测试用例能发现真实缺陷」：

| 缺陷 | 现象 | 捕获用例 |
|---|---|---|
| D1 | 编辑账单金额后，月度统计汇总不刷新 | `test_edit_bill_updates_stats`、`test_edit_bill_reflects_in_stats` |
| D2 | 备注含 `<script>` 标签时页面渲染异常（XSS） | `test_add_bill_special_note` |
| D3 | 分类重名时不提示"已存在"而报"未知错误" | `test_add_duplicate_category` |

验证（正常模式全绿）：

```powershell
$env:SEED_BUGS = "0"; .\.venv\Scripts\python -m pytest          # 54 passed，捕获缺陷的用例全绿
$env:SEED_BUGS = "1"; .\.venv\Scripts\python -m pytest -m p1    # D1/D2/D3 用例失败 = 缺陷被发现
```

> 测试运行默认 `SEED_BUGS=0`（常规回归保持全绿）；`SEED_BUGS=1` 用于演示缺陷捕获能力。

## 测试用例设计要点

- **用例隔离**：每个用例前通过 `/api/dev/reset` 重置数据库并写入种子数据，互不影响
- **接口造数**：前置数据用 API 快速准备（`api/factories.py`），避免 UI 重复操作降低稳定性
- **数据驱动**：YAML 文件驱动非法输入等重复场景（`data/*.yaml`）
- **异步等待**：依赖 Playwright 自动等待与 `expect` 断言，避免 `sleep`
- **失败定位**：失败自动全页截图（Allure 附件）+ trace 录屏 + 视频
- **分屏浏览器**：默认 Chromium，可参数化多浏览器/移动端

## 简历亮点话术

> **MoneyKeeper UI 自动化测试平台**（个人项目）
> - 自研 FastAPI 记账应用作为被测对象，独立完成 54 条 UI 自动化用例（POM 设计模式 + YAML 数据驱动）
> - 基于 Playwright + Pytest 构建测试框架，实现失败自动截图/录屏、用例隔离（接口造数）、Allure 报告
> - 集成 GitHub Actions，PR 自动回归 + 每日定时全量，报告自动部署 GitHub Pages
> - 通过用例真实捕获 3 个隐藏缺陷（金额汇总、XSS 特殊字符、分类重名）

## 文档

- 详细设计：`docs/project_design.md`