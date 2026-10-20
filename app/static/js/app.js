/* MoneyKeeper 前端：极简 SPA */
const state = {
  token: localStorage.getItem("mk_token") || "",
  username: localStorage.getItem("mk_username") || "",
  view: "bills",
  billsPage: 1,
  billFilters: { category_id: "", month: "", keyword: "" },
};

const app = document.getElementById("app");

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers["X-Token"] = state.token;
  const res = await fetch("/api" + path, { ...options, headers });
  let data = null;
  try { data = await res.json(); } catch (_) { /* 非 JSON */ }
  if (!res.ok) {
    const detail = data && data.detail ? data.detail : "请求失败";
    if (res.status === 401) { state.token = ""; localStorage.clear(); render(); }
    throw new Error(detail);
  }
  return data;
}

/* ---------- 认证视图 ---------- */
function renderAuth(isRegister) {
  app.innerHTML = `
    <div class="auth-card">
      <h1>${isRegister ? "注册" : "登录"} MoneyKeeper</h1>
      <div class="form-item"><label>用户名</label>
        <input data-testid="${isRegister ? "register-username" : "login-username"}" id="username" autocomplete="username"></div>
      <div class="form-item"><label>密码</label>
        <input data-testid="${isRegister ? "register-password" : "login-password"}" id="password" type="password" autocomplete="current-password"></div>
      <button class="btn" data-testid="${isRegister ? "register-submit" : "login-submit"}" id="submit">${isRegister ? "注册并登录" : "登录"}</button>
      <div class="error" data-testid="${isRegister ? "register-error" : "login-error"}" id="error"></div>
      <div class="muted" style="margin-top:12px">
        <a href="#" data-testid="${isRegister ? "register-to-login" : "login-to-register"}" id="switch">${isRegister ? "已有账号？去登录" : "没有账号？去注册"}</a>
      </div>
    </div>`;
  document.getElementById("submit").onclick = async () => {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    try {
      if (isRegister) {
        await api("/auth/register", { method: "POST", body: JSON.stringify({ username, password }) });
      }
      const data = await api("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
      state.token = data.token;
      state.username = data.username;
      localStorage.setItem("mk_token", data.token);
      localStorage.setItem("mk_username", data.username);
      render();
    } catch (e) { document.getElementById("error").textContent = e.message; }
  };
  document.getElementById("switch").onclick = (e) => { e.preventDefault(); renderAuth(!isRegister); };
  document.getElementById("username").focus();
}

/* ---------- 主界面 ---------- */
function renderApp() {
  app.innerHTML = `
    <div class="topbar">
      <h1>MoneyKeeper</h1>
      <div class="row">
        <span class="muted" data-testid="app-username">${esc(state.username)}</span>
        <button class="btn secondary sm" data-testid="logout-btn" id="logout">退出</button>
      </div>
    </div>
    <div class="tabs">
      <div class="tab ${state.view === "bills" ? "active" : ""}" data-testid="tab-bills" data-view="bills">账单</div>
      <div class="tab ${state.view === "categories" ? "active" : ""}" data-testid="tab-categories" data-view="categories">分类</div>
      <div class="tab ${state.view === "stats" ? "active" : ""}" data-testid="tab-stats" data-view="stats">统计</div>
      <div class="tab ${state.view === "settings" ? "active" : ""}" data-testid="tab-settings" data-view="settings">设置</div>
    </div>
    <div id="view"></div>`;

  document.getElementById("logout").onclick = async () => {
    try { await api("/auth/logout", { method: "POST" }); } catch (_) { /* 忽略 */ }
    state.token = ""; localStorage.clear(); render();
  };
  document.querySelectorAll(".tab").forEach((t) => {
    t.onclick = () => { state.view = t.dataset.view; renderApp(); };
  });
  renderView();
}

function renderView() {
  const el = document.getElementById("view");
  if (state.view === "bills") renderBills(el);
  else if (state.view === "categories") renderCategories(el);
  else if (state.view === "stats") renderStats(el);
  else renderSettings(el);
}

/* ---------- 账单 ---------- */
async function renderBills(el) {
  const today = new Date().toISOString().slice(0, 10);
  const curMonth = today.slice(0, 7);
  el.innerHTML = `
    <div class="card">
      <h2>记一笔</h2>
      <div class="row">
        <select data-testid="bill-category" id="bill-category"></select>
        <input data-testid="bill-amount" id="bill-amount" type="number" step="0.01" min="0.01" placeholder="金额" style="width:100px">
        <input data-testid="bill-note" id="bill-note" placeholder="备注" style="width:140px">
        <input data-testid="bill-date" id="bill-date" type="date" value="${today}" style="width:140px">
        <button class="btn" data-testid="bill-submit" id="bill-submit">保存</button>
      </div>
      <div class="error" data-testid="bill-error" id="bill-error"></div>
    </div>
    <div class="card">
      <h2>账单列表</h2>
      <div class="row filters">
        <select data-testid="bill-filter-category" id="filter-category"></select>
        <input data-testid="bill-filter-month" id="filter-month" type="month" value="${state.billFilters.month || curMonth}">
        <input data-testid="bill-filter-keyword" id="filter-keyword" placeholder="搜索备注" value="${esc(state.billFilters.keyword)}">
        <button class="btn secondary sm" data-testid="bill-filter-reset" id="filter-reset">重置</button>
      </div>
      <div data-testid="bill-list" id="bill-list"></div>
      <div class="pagination">
        <button class="btn secondary sm" data-testid="bill-page-prev" id="page-prev">上一页</button>
        <span data-testid="bill-page-info" id="page-info"></span>
        <button class="btn secondary sm" data-testid="bill-page-next" id="page-next">下一页</button>
      </div>
    </div>`;

  const categories = await api("/categories");
  const catOpts = (sel) => {
    sel.innerHTML = '<option value="">全部</option>' +
      categories.map((c) => `<option value="${c.id}">${esc(c.name)}（${c.type === "income" ? "收入" : "支出"}）</option>`).join("");
  };
  catOpts(document.getElementById("bill-category"));
  catOpts(document.getElementById("filter-category"));

  document.getElementById("bill-submit").onclick = async () => {
    const payload = {
      category_id: Number(document.getElementById("bill-category").value),
      amount: Number(document.getElementById("bill-amount").value),
      note: document.getElementById("bill-note").value,
      bill_date: document.getElementById("bill-date").value,
    };
    try {
      if (!payload.category_id) throw new Error("请选择分类");
      if (!(payload.amount > 0)) throw new Error("金额必须大于 0");
      await api("/bills", { method: "POST", body: JSON.stringify(payload) });
      document.getElementById("bill-amount").value = "";
      document.getElementById("bill-note").value = "";
      await loadBills();
    } catch (e) { document.getElementById("bill-error").textContent = e.message; }
  };

  const doFilter = async (reset = false) => {
    if (reset) { state.billFilters = { category_id: "", month: "", keyword: "" }; document.getElementById("filter-month").value = curMonth; document.getElementById("filter-keyword").value = ""; }
    else state.billFilters = {
      category_id: document.getElementById("filter-category").value,
      month: document.getElementById("filter-month").value,
      keyword: document.getElementById("filter-keyword").value.trim(),
    };
    state.billsPage = 1;
    await loadBills();
  };
  document.getElementById("filter-reset").onclick = () => doFilter(true);
  document.getElementById("filter-keyword").onchange = () => doFilter(false);
  document.getElementById("filter-category").onchange = () => doFilter(false);
  document.getElementById("filter-month").onchange = () => doFilter(false);

  document.getElementById("page-prev").onclick = async () => { if (state.billsPage > 1) { state.billsPage--; await loadBills(); } };
  document.getElementById("page-next").onclick = async () => { state.billsPage++; await loadBills(); };

  async function loadBills() {
    const q = new URLSearchParams({ page: state.billsPage, page_size: 10 });
    if (state.billFilters.category_id) q.set("category_id", state.billFilters.category_id);
    if (state.billFilters.month) q.set("month", state.billFilters.month);
    if (state.billFilters.keyword) q.set("keyword", state.billFilters.keyword);
    const data = await api("/bills?" + q.toString());
    const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));
    document.getElementById("page-info").textContent = `第 ${data.page}/${totalPages} 页 · 共 ${data.total} 条`;
    document.getElementById("page-prev").disabled = data.page <= 1;
    document.getElementById("page-next").disabled = data.page >= totalPages;

    const list = document.getElementById("bill-list");
    if (!data.items.length) {
      list.innerHTML = '<div class="muted">暂无账单</div>';
      return;
    }
    // 注意：note 使用 innerHTML 渲染（缺陷 D2 埋点，正文禁止 XSS）
    list.innerHTML = data.items.map((b) => `
      <div class="list-item" data-testid="bill-row-${b.id}">
        <div>
          <div>${esc(b.category_name)} · <span data-testid="bill-note-${b.id}">${b.note}</span></div>
          <div class="muted">${b.bill_date}</div>
        </div>
        <div class="row">
          <span class="amount ${b.category_type}" data-testid="bill-amount-${b.id}">${b.category_type === "income" ? "+" : "-"}${b.amount.toFixed(2)}</span>
          <button class="btn secondary sm" data-testid="bill-edit-${b.id}" data-id="${b.id}">编辑</button>
          <button class="btn danger sm" data-testid="bill-del-${b.id}" data-id="${b.id}">删除</button>
        </div>
      </div>`).join("");

    list.querySelectorAll("[data-id]").forEach((btn) => {
      btn.onclick = async () => {
        const id = btn.dataset.id;
        if (btn.textContent === "删除") {
          if (!confirm("确定删除该账单？")) return;
          await api("/bills/" + id, { method: "DELETE" });
          await loadBills();
        } else {
          const bill = data.items.find((b) => b.id === Number(id));
          const note = prompt("编辑备注", bill.note);
          if (note === null) return;
          await api("/bills/" + id, {
            method: "PUT",
            body: JSON.stringify({ category_id: bill.category_id, amount: bill.amount, note, bill_date: bill.bill_date }),
          });
          await loadBills();
        }
      };
    });
  }
  await loadBills();
}

/* ---------- 分类 ---------- */
async function renderCategories(el) {
  el.innerHTML = `
    <div class="card">
      <h2>新增分类</h2>
      <div class="row">
        <input data-testid="cat-name" id="cat-name" placeholder="分类名称" style="width:160px">
        <select data-testid="cat-type" id="cat-type">
          <option value="expense">支出</option>
          <option value="income">收入</option>
        </select>
        <button class="btn" data-testid="cat-submit" id="cat-submit">保存</button>
      </div>
      <div class="error" data-testid="cat-error" id="cat-error"></div>
    </div>
    <div class="card">
      <h2>分类列表</h2>
      <div data-testid="cat-list" id="cat-list"></div>
    </div>`;

  document.getElementById("cat-submit").onclick = async () => {
    try {
      await api("/categories", {
        method: "POST",
        body: JSON.stringify({ name: document.getElementById("cat-name").value, type: document.getElementById("cat-type").value }),
      });
      document.getElementById("cat-name").value = "";
      await loadCats();
    } catch (e) { document.getElementById("cat-error").textContent = e.message; }
  };

  async function loadCats() {
    const rows = await api("/categories");
    const list = document.getElementById("cat-list");
    if (!rows.length) { list.innerHTML = '<div class="muted">暂无分类</div>'; return; }
    list.innerHTML = rows.map((c) => `
      <div class="list-item" data-testid="cat-row-${c.id}">
        <span>${esc(c.name)} <span class="muted">${c.type === "income" ? "收入" : "支出"}</span></span>
        <span class="row">
          <button class="btn secondary sm" data-testid="cat-del-${c.id}" data-id="${c.id}">删除</button>
        </span>
      </div>`).join("");
    list.querySelectorAll("[data-id]").forEach((btn) => {
      btn.onclick = async () => {
        if (!confirm("确定删除该分类？")) return;
        try {
          await api("/categories/" + btn.dataset.id, { method: "DELETE" });
          await loadCats();
        } catch (e) { document.getElementById("cat-error").textContent = e.message; }
      };
    });
  }
  await loadCats();
}

/* ---------- 统计 ---------- */
async function renderStats(el) {
  const curMonth = new Date().toISOString().slice(0, 7);
  el.innerHTML = `
    <div class="card">
      <div class="row">
        <input data-testid="stats-month" id="stats-month" type="month" value="${curMonth}">
        <button class="btn" data-testid="stats-load" id="stats-load">查询</button>
      </div>
    </div>
    <div class="stat-grid">
      <div class="stat-box"><div class="label">收入</div><div class="value" data-testid="stats-income" id="stats-income">-</div></div>
      <div class="stat-box"><div class="label">支出</div><div class="value" data-testid="stats-expense" id="stats-expense">-</div></div>
      <div class="stat-box"><div class="label">结余</div><div class="value" data-testid="stats-balance" id="stats-balance">-</div></div>
    </div>
    <div class="card">
      <h2>分类汇总</h2>
      <div data-testid="stats-category-list" id="stats-cat"></div>
    </div>`;

  async function loadStats() {
    const month = document.getElementById("stats-month").value || curMonth;
    const data = await api("/stats/monthly?month=" + month);
    document.getElementById("stats-income").textContent = "+" + data.income.toFixed(2);
    document.getElementById("stats-expense").textContent = "-" + data.expense.toFixed(2);
    document.getElementById("stats-balance").textContent = data.balance.toFixed(2);
    const box = document.getElementById("stats-cat");
    if (!data.by_category.length) { box.innerHTML = '<div class="muted">本月暂无数据</div>'; return; }
    box.innerHTML = data.by_category.map((c) => `
      <div class="list-item" data-testid="stats-cat-${c.category_id}">
        <span>${esc(c.name)} <span class="muted">${c.type === "income" ? "收入" : "支出"}</span></span>
        <span class="amount ${c.type}">${c.type === "income" ? "+" : "-"}${c.total.toFixed(2)}</span>
      </div>`).join("");
  }
  document.getElementById("stats-load").onclick = loadStats;
  await loadStats();
}

/* ---------- 设置 ---------- */
function renderSettings(el) {
  el.innerHTML = `
    <div class="card">
      <h2>修改密码</h2>
      <div class="form-item"><label>原密码</label>
        <input data-testid="set-old" id="set-old" type="password"></div>
      <div class="form-item"><label>新密码</label>
        <input data-testid="set-new" id="set-new" type="password"></div>
      <button class="btn" data-testid="set-submit" id="set-submit">修改</button>
      <div class="error" data-testid="set-msg" id="set-msg"></div>
    </div>`;
  document.getElementById("set-submit").onclick = async () => {
    try {
      await api("/auth/password", {
        method: "PUT",
        body: JSON.stringify({
          old_password: document.getElementById("set-old").value,
          new_password: document.getElementById("set-new").value,
        }),
      });
      document.getElementById("set-msg").textContent = "修改成功，请重新登录";
      document.getElementById("set-msg").style.color = "#2f9e44";
      state.token = ""; localStorage.clear();
      setTimeout(render, 1200);
    } catch (e) {
      document.getElementById("set-msg").textContent = e.message;
      document.getElementById("set-msg").style.color = "";
    }
  };
}

function render() {
  if (state.token) renderApp();
  else renderAuth(false);
}

render();
