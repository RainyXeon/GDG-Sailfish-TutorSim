// Điểm vào: định tuyến theo hash (#/...), khung giao diện theo vai, menu tài khoản, công tắc sáng/tối.
import { api, hasToken, logout, setOnUnauthorized } from "./api.js";
import { $, $$, esc, IMG, toast, formDialog, fmtScore } from "./ui.js";
import * as auth from "./views/auth.js";
import * as student from "./views/student.js";
import * as tutor from "./views/tutor.js";
import * as manager from "./views/manager.js";

const app = document.getElementById("app");
export const state = { user: null };

// ---------- công tắc sáng / tối ----------
export function toggleTheme() {
  const root = document.documentElement;
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  try { localStorage.setItem("tutorsim_theme", next); } catch { /* bỏ qua */ }
}

// ---------- điều hướng ----------
const NAV = {
  student: [["s/home", "Trang chủ", "ic-home"], ["s/exams", "Làm bài", "ic-check"], ["s/results", "Kết quả", "ic-bar"]],
  tutor: [["t/home", "Trang chủ", "ic-home"], ["t/practice", "Luyện tập", "ic-book"], ["t/reports", "Báo cáo", "ic-chart"]],
  manager: [["m/overview", "Tổng quan", "ic-pie"], ["m/tutors", "Gia sư", "ic-bookc"], ["m/knowledge", "Kiến thức", "ic-book"], ["m/stats", "Thống kê", "ic-bar"]],
};
const HOME = { student: "s/home", tutor: "t/home", manager: "m/overview" };
const AVATAR = { student: "shark-student.svg", tutor: "shark-tutor.svg", manager: "shark-admin.svg" };
const ROLE_LABEL = { student: "Học sinh", tutor: "Gia sư", manager: "Quản lý" };

const ROUTES = [
  // [mẫu đường dẫn, vai được vào, hàm vẽ, mục nav đang chọn]
  ["login", null, auth.login], ["register", null, auth.register], ["forgot", null, auth.forgot],
  ["s/home", "student", student.home, "s/home"], ["s/exams", "student", student.exams, "s/exams"],
  ["s/exam/:id", "student", student.exam, "s/exams", true], ["s/results", "student", student.results, "s/results"],
  ["s/result/:id", "student", student.result, "s/results"],
  ["t/home", "tutor", tutor.home, "t/home"], ["t/practice", "tutor", tutor.practiceIndex, "t/practice"],
  ["t/practice/:id", "tutor", tutor.practice, "t/practice"], ["t/reports", "tutor", tutor.reports, "t/reports"],
  ["t/report/:id", "tutor", tutor.report, "t/reports"],
  ["m/overview", "manager", manager.overview, "m/overview"], ["m/tutors", "manager", manager.tutors, "m/tutors"],
  ["m/tutors/:id", "manager", manager.tutors, "m/tutors"], ["m/report/:id", "manager", tutor.report, "m/tutors"],
  ["m/knowledge", "manager", manager.knowledge, "m/knowledge"], ["m/knowledge/:cd", "manager", manager.knowledgeDetail, "m/knowledge"],
  ["m/stats", "manager", manager.stats, "m/stats"], ["m/stats/:cd", "manager", manager.statsTopic, "m/stats"],
  ["m/account", "manager", manager.account, null],
];

export function go(path) {
  const target = "#/" + path.replace(/^#?\/?/, "");
  if (location.hash === target) render(); else location.hash = target;
}

function match(hashPath) {
  for (const [pattern, role, view, nav, guard] of ROUTES) {
    const a = pattern.split("/"), b = hashPath.split("/");
    if (a.length !== b.length) continue;
    const params = {};
    if (a.every((seg, i) => (seg.startsWith(":") ? ((params[seg.slice(1)] = decodeURIComponent(b[i])), true) : seg === b[i]))) {
      return { role, view, nav, params, guard };
    }
  }
  return null;
}

let cleanup = null;
let leaveGuard = null; // hàm trả về true nếu được phép rời trang (dùng cho màn làm bài)
export const setLeaveGuard = (fn) => { leaveGuard = fn; };

async function render() {
  const raw = location.hash.replace(/^#\/?/, "");
  const [path, qs] = raw.split("?");
  const query = Object.fromEntries(new URLSearchParams(qs || ""));
  if (typeof cleanup === "function") { try { cleanup(); } catch { /* bỏ qua */ } }
  cleanup = null; leaveGuard = null;
  closeMenu();

  const user = state.user;
  let m = match(path);
  if (!user) {
    if (!m || m.role) { if (path !== "login") return go("login"); m = match("login"); }
  } else if (!m || (m.role && m.role !== user.role) || !m.role) {
    return go(HOME[user.role]);
  }

  if (!m.role) {
    app.innerHTML = "";
    cleanup = await m.view(app, { query, go });
    mountToggle();
    return;
  }
  app.innerHTML = shellHtml(user, m.nav);
  bindShell(user);
  const main = $(".main", app);
  main.innerHTML = `<div class="spinner" role="status" aria-label="Đang tải"></div>`;
  try {
    cleanup = await m.view(main, { user, params: m.params, query, go, refreshUser });
  } catch (e) {
    main.innerHTML = `<div class="card"><div class="notice error"><span class="i">!</span><div class="grow">${esc(e.message)}</div>
      <button class="btn outline danger" id="retry">Thử lại</button></div></div>`;
    $("#retry", main).addEventListener("click", render);
  }
  mountToggle();
}

function shellHtml(user, nav) {
  return `
  <div class="shell">
    <nav class="nav" aria-label="Điều hướng chính">
      <button class="nav-logo" data-go="${HOME[user.role]}" aria-label="TutorSim – Trang chủ"><img src="${IMG}logo-shark.svg" alt="" /></button>
      <div class="nav-items">
        ${NAV[user.role].map(([p, label, ic]) => `
          <a class="nav-item" href="#/${p}" ${p === nav ? 'aria-current="page"' : ""}>
            <span class="ic-wrap"><i class="ic ${ic}" aria-hidden="true"></i></span>${label}</a>`).join("")}
      </div>
      <button class="nav-avatar" id="avatar-btn" aria-haspopup="dialog" aria-label="Tài khoản của ${esc(user.name)}">
        <img src="${IMG}${AVATAR[user.role]}" alt="" /></button>
    </nav>
    <main class="main ${user.role}" id="main"></main>
  </div>`;
}

function bindShell(user) {
  $$("[data-go]", app).forEach((b) => b.addEventListener("click", () => go(b.dataset.go)));
  $("#avatar-btn", app).addEventListener("click", (e) => { e.stopPropagation(); openMenu(user); });
  // màn làm bài: hỏi trước khi rời
  $$(".nav a, .nav button[data-go]", app).forEach((a) => a.addEventListener("click", async (e) => {
    if (leaveGuard && !(await leaveGuard())) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true));
}

function mountToggle() {
  let t = document.getElementById("mode-toggle");
  if (!t) {
    t = document.createElement("button");
    t.id = "mode-toggle"; t.className = "mode-toggle";
    t.addEventListener("click", () => { toggleTheme(); label(); });
    document.body.appendChild(t);
  }
  const label = () => t.setAttribute("aria-label", document.documentElement.dataset.theme === "dark" ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối");
  label();
}

// ---------- menu tài khoản (nhấp avatar) ----------
function closeMenu() { $("#acct-menu")?.remove(); document.removeEventListener("click", outside); }
function outside(e) { if (!e.target.closest("#acct-menu")) closeMenu(); }
async function openMenu(user) {
  if ($("#acct-menu")) return closeMenu();
  const el = document.createElement("div");
  el.id = "acct-menu"; el.className = "menu"; el.setAttribute("role", "dialog"); el.setAttribute("aria-label", "Tài khoản");
  const rows = [["Vai trò", ROLE_LABEL[user.role]], ["Tên đăng nhập", user.username]];
  if (user.role === "tutor") rows.unshift(["Mã gia sư", user.code]);
  el.innerHTML = `
    <div class="top"><span class="avatar" style="width:48px;height:48px"><img src="${IMG}${AVATAR[user.role]}" alt="" /></span>
      <div><b>${esc(user.name)}</b><span>${user.role === "tutor" ? "Gia sư môn Toán THPT" : user.role === "student" ? "Học sinh lớp 12 · Môn Toán" : "Quản lý hệ thống TutorSim"}</span></div></div>
    <dl id="menu-dl">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("")}</dl>
    <div class="acts">
      ${user.role === "manager" ? `<button class="btn tonal" data-a="account">Cài đặt tài khoản</button>` : ""}
      <button class="btn tonal" data-a="name">Đổi tên hiển thị</button>
      <button class="btn tonal" data-a="pw">Đổi mật khẩu</button>
      <button class="btn outline danger" data-a="logout">Đăng xuất</button>
    </div>`;
  document.body.appendChild(el);
  setTimeout(() => document.addEventListener("click", outside), 0);
  el.addEventListener("click", (e) => {
    const a = e.target.closest("[data-a]")?.dataset.a;
    if (!a) return;
    closeMenu();
    if (a === "logout") signOut();
    if (a === "account") go("m/account");
    if (a === "name") changeName();
    if (a === "pw") changePassword();
  });
  // số liệu bổ sung theo vai
  try {
    const dl = $("#menu-dl", el);
    if (user.role === "tutor") {
      const st = await api.tutorStats(user.id);
      dl.insertAdjacentHTML("beforeend", `<dt>Số buổi đã luyện</dt><dd>${st.sessions_count} buổi</dd><dt>Điểm trung bình</dt><dd>${st.avg_total == null ? "–" : fmtScore(st.avg_total) + "/4"}</dd>`);
    } else if (user.role === "student") {
      const s = await api.studentSummary(user.id);
      dl.insertAdjacentHTML("beforeend", `<dt>Đề đã hoàn thành</dt><dd>${s.stats?.exams_done ?? 0} đề</dd><dt>Trạng thái</dt><dd>Đang hoạt động</dd>`);
    }
  } catch { /* menu vẫn dùng được khi thiếu số liệu */ }
}

export function changeName() {
  formDialog({
    title: "Đổi tên hiển thị", ok: "Lưu",
    fields: [{ name: "name", label: "Tên hiển thị", value: state.user.name }],
    onSubmit: async ({ name }) => {
      try { state.user = await api.updateMe(name); toast("Đã đổi tên hiển thị."); render(); return null; } catch (e) { return e.message; }
    },
  });
}
export function changePassword() {
  formDialog({
    title: "Đổi mật khẩu", ok: "Đổi mật khẩu",
    fields: [
      { name: "old", label: "Mật khẩu hiện tại", type: "password", autocomplete: "current-password" },
      { name: "new1", label: "Mật khẩu mới (ít nhất 8 ký tự)", type: "password", autocomplete: "new-password" },
      { name: "new2", label: "Nhập lại mật khẩu mới", type: "password", autocomplete: "new-password" },
    ],
    onSubmit: async ({ old, new1, new2 }) => {
      if (new1.length < 8) return "Mật khẩu mới cần ít nhất 8 ký tự.";
      if (new1 !== new2) return "Hai lần nhập mật khẩu mới chưa khớp.";
      try { await api.changePassword(old, new1); toast("Đã đổi mật khẩu."); return null; } catch (e) { return e.message; }
    },
  });
}

export function signOut() { logout(); state.user = null; go("login"); }
async function refreshUser() { state.user = await api.me(); return state.user; }
export function onLoggedIn(user) { state.user = user; go(HOME[user.role]); }

// ---------- khởi động ----------
setOnUnauthorized(() => {
  if (state.user) toast("Phiên đăng nhập đã hết hạn, hãy đăng nhập lại.");
  state.user = null; go("login");
});
window.addEventListener("hashchange", render);
(async () => {
  if (hasToken()) {
    app.innerHTML = `<div class="spinner" role="status" aria-label="Đang tải"></div>`;
    try { state.user = await api.me(); } catch { logout(); }
  }
  render();
})();
