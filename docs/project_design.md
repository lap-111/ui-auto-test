# MoneyKeeper UI 自动化测试平台 — 项目设计文档

> 版本：v1.0 ｜ 状态：已确认 ｜ 日期：2026-10-20

## 1. 项目概述

自建记账 Web 应用（MoneyKeeper）作为被测对象，配套一套完整工程级的 Playwright UI 自动化测试框架，形成「被测应用 → 自动化框架 → 测试报告 → CI 持续回归」的完整闭环。

**项目目标**：练熟 UI 自动化核心技术（POM、数据驱动、断言设计、失败定位），产出可演示、有量化指标、可写进简历的个人项目。

**核心亮点**：
- 被测对象自研，完全可控（造数据、重置环境、注入缺陷）
- 被测应用故意埋 2~3 个隐藏缺陷，由测试用例真实捕获，证明用例有效性
- 框架支持失败自动截图/录屏、测试隔离（接口造数）、Allure 报告、CI 全自动

## 2. 技术栈

| 领域 | 选型 |
|---|---|
| 被测应用 | Python 3.11 + FastAPI + SQLite + 原生 HTML/JS |
| 测试框架 | Playwright + Pytest |
| 数据驱动 | YAML + pytest parametrize |
| 报告 | Allure 2 + 失败截图/录屏（trace） |
| CI | GitHub Actions（PR 触发回归 + 每日定时全量） |
| 包管理 | venv + requirements.txt |

## 3. 被测应用设计（MoneyKeeper）

### 3.1 功能模块

| 模块 | 功能 | 关键交互点 |
|---|---|---|
| 用户 auth | 注册 / 登录 / 登出 / 修改密码 | 表单校验、错误提示 |
| 记账 bill | 新增 / 编辑 / 删除 / 按类别日期筛选 / 分页 | CRUD、金额、校验 |
| 分类 category | 支出/收入分类管理 | 增删改、重名校验 |
| 报表 stats | 月度收支统计、图表 | 数值断言 |

### 3.2 数据库（SQLite）

- `users(id, username, password_hash, created_at)`
- `categories(id, user_id, name, type[income/expense], created_at)`
- `bills(id, user_id, category_id, amount, note, bill_date, created_at)`

### 3.3 API 清单（含造数接口）

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录（返回 token） |
| POST | /api/auth/logout | 登出 |
| PUT | /api/auth/password | 修改密码 |
| GET/POST | /api/categories | 分类列表 / 新增 |
| PUT/DELETE | /api/categories/{id} | 改 / 删分类 |
| GET/POST | /api/bills | 记账列表（支持筛选、分页）/ 新增 |
| PUT/DELETE | /api/bills/{id} | 改 / 删账单 |
| GET | /api/stats/monthly?month= | 月度统计 |
| POST | /api/dev/reset | **仅测试环境**：重置数据库并写入种子数据（造数接口） |

### 3.4 隐藏缺陷清单（埋点，供用例捕获）

| # | 缺陷 | 所属功能 | 预期被用例发现 |
|---|---|---|---|
| D1 | 编辑账单金额后，当月统计汇总不刷新（仍用旧值） | 报表 | 编辑→报表数值断言 |
| D2 | 账单备注输入含 `<script>` 标签时页面渲染异常 | 记账 | 特殊字符输入用例 |
| D3 | 分类重名时提示不准确（显示"未知错误"） | 分类 | 重名校验用例 |

> 缺陷通过环境变量 `SEED_BUGS=1` 控制注入，测试运行环境默认开启。

## 4. 测试框架设计

### 4.1 分层架构（POM 页面对象模式）

```
ui_auto_test/
├── app/                      # 被测应用（FastAPI 记账本）
│   ├── main.py               # 应用入口
│   ├── db.py                 # SQLite 数据层
│   ├── routers/              # 路由：auth / bills / categories / stats
│   ├── seed.py               # 种子数据 + 缺陷注入
│   └── static/               # 前端页面（HTML/JS）
├── tests/                    # ① 用例层：只写「步骤 + 断言」
│   ├── conftest.py           # 全局 fixture
│   ├── test_auth.py
│   ├── test_bills.py
│   ├── test_categories.py
│   └── test_stats.py
├── pages/                    # ② 页面对象层：一页一类
│   ├── login_page.py
│   ├── register_page.py
│   ├── bill_page.py
│   ├── category_page.py
│   └── stats_page.py
├── base/                     # ③ 基础层
│   ├── base_page.py          # 公共页面操作/断言
│   └── base_api.py           # 接口造数基类
├── api/                      # ④ 接口层：前置造数、后置清理
├── data/                     # ⑤ 数据层：yaml 数据驱动
│   ├── auth_data.yaml
│   └── bill_data.yaml
├── utils/                    # ⑥ 工具层：随机数据工厂、日志、路径
├── pytest.ini                # 标记：smoke / regression / p0~p1
├── requirements.txt
├── allure-results/           # 报告原始数据（gitignore）
├── .github/workflows/
│   └── ui-test.yml           # CI/CD
└── README.md
```

### 4.2 核心机制

| 机制 | 设计 |
|---|---|
| 浏览器管理 | conftest fixture；`--headed/--headless`；Chromium/Firefox/WebKit 参数化；移动端视口 |
| 自动等待 | Playwright 内置等待 + `expect` 断言，禁止 sleep |
| 失败处理 | 失败自动截图 + trace 录屏 + 重试 1 次 |
| 数据驱动 | YAML + parametrize |
| 测试隔离 | 每用例 API 重置数据库/造独立数据 |
| 用例标记 | smoke（冒烟）/ regression（全量）/ p0 / p1 |
| 报告 | Allure：步骤、附件、分类、趋势 |
| 日志 | logging 输出到 test 运行日志 |

### 4.3 用例清单（目标 50+）

| 模块 | 用例示例 | 条数 |
|---|---|---|
| auth | 正确登录、错误密码、空值校验、密码边界、重复注册、修改密码流程 | ~12 |
| bills | 新增（正常/边界/特殊字符 D2）、编辑（D1 联动报表）、删除、筛选、分页 | ~20 |
| categories | 增删改、重名校验（D3）、类型过滤 | ~10 |
| stats | 月度切换、数值断言、空数据、含缺陷汇总验证 | ~8 |
| 其他 | 未登录拦截、响应式布局冒烟 | ~5 |

## 5. CI/CD 设计

- `.github/workflows/ui-test.yml`：
  - 触发：push / pull_request（跑 smoke）、定时 cron 每日 02:00（跑全量）
  - 步骤：checkout → setup-python → install → install playwright → 启动 app → 跑 pytest → 上传 Allure 报告 → 部署 GitHub Pages
- 报告地址固定为 GitHub Pages 链接，供简历/面试展示。

## 6. 里程碑与验收标准

| 阶段 | 内容 | 验收标准 | 提交规范示例 |
|---|---|---|---|
| P0 | 设计文档 | 方案评审通过 | docs: 新增项目设计文档 |
| P1 | 被测应用开发 | 应用可运行、核心流程手动可走通、造数接口可用 | feat: 搭建记账应用 Mock 服务 |
| P2 | 框架骨架 | 登录 + 新增记账 2 条冒烟用例跑通 | feat: 搭建测试框架骨架 |
| P3 | 全量用例 | 50+ 用例全绿，失败可定位（截图/录屏） | test: 补充全模块测试用例 |
| P4 | 报告 + CI | push 自动跑、报告在线可看 | ci: 集成 GitHub Actions 与 Allure |
| P5 | 交付 | README、演示录屏、简历话术 | docs: 完善项目文档 |

## 7. 简历亮点话术（P5 使用）

> **MoneyKeeper UI 自动化测试平台**（个人项目）
> - 自研 FastAPI 记账应用作为被测对象，独立完成 50+ 条 UI 自动化用例（POM 设计模式 + YAML 数据驱动）
> - 基于 Playwright + Pytest 构建测试框架，实现失败自动截图/录屏、用例隔离（接口造数）、Allure 报告
> - 集成 GitHub Actions，PR 自动回归 + 每日定时全量，报告自动部署 GitHub Pages
> - 通过用例真实捕获 3 个隐藏缺陷（金额汇总、特殊字符等）
