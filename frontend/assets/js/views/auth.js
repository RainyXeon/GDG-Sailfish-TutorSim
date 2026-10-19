// Đăng nhập, đăng ký, quên mật khẩu (theo Figma 01 • Đăng nhập & Đăng ký, 14 • Quên mật khẩu).
import { api } from "../api.js";
import { $, $$, esc, IMG } from "../ui.js";
import { onLoggedIn } from "../app.js";

function frame(root, { tag1, tag2, tag3, card, decos = "" }) {
  root.innerHTML = `
  <div class="auth">
    <section class="auth-intro" aria-hidden="false">
      <p class="brand">TutorSim</p>
      <p class="tag1">${tag1}</p>
      <p class="tag2">${tag2}</p>
      <p class="tag3">${tag3}</p>
      <img class="mascot" src="${IMG}shark-hi.svg" alt="" />
      ${decos}
    </section>
    <section class="auth-side">
      <div class="auth-card">${card}</div>
    </section>
  </div>`;
}

const field = (name, label, type, placeholder, extra = "") => `
  <div><label class="tf" data-f="${name}"><span>${label}</span>
    <input name="${name}" type="${type}" placeholder="${placeholder}" ${extra} required /></label>
    <span class="tf-error hidden" data-err="${name}"></span></div>`;

function showErrors(form, map) {
  $$(".tf", form).forEach((t) => t.classList.remove("invalid"));
  $$(".tf-error", form).forEach((e) => e.classList.add("hidden"));
  for (const [k, msg] of Object.entries(map)) {
    $(`[data-f="${k}"]`, form)?.classList.add("invalid");
    const e = $(`[data-err="${k}"]`, form);
    if (e) { e.textContent = msg; e.classList.remove("hidden"); }
  }
}

export async function login(root, { go }) {
  frame(root, {
    tag1: "Đồng hành cùng", tag2: "những người dạy học.",
    tag3: "Một không gian luyện giảng tập trung, được thiết kế để phản hồi rõ ràng.",
    card: `
      <h1>Chào mừng trở lại</h1>
      <p class="sub">Đăng nhập để tiếp tục sử dụng TutorSim.</p>
      <p class="sub2">Sử dụng tài khoản đã đăng ký để tiếp tục</p>
      <form class="auth-form" novalidate>
        ${field("username", "Tên đăng nhập", "text", "Nhập tên đăng nhập", 'autocomplete="username" autocapitalize="none" spellcheck="false"')}
        ${field("password", "Mật khẩu", "password", "Nhập mật khẩu", 'autocomplete="current-password"')}
        <p class="form-error hidden" role="alert" id="form-err"></p>
        <div class="auth-actions">
          <button class="btn strong" type="submit">Đăng nhập</button>
          <button class="link label-l" type="button" data-to="forgot" style="color:var(--muted)">Quên mật khẩu?</button>
        </div>
      </form>
      <div class="auth-foot">
        <button class="link" type="button" data-to="register" id="to-register">Chưa có tài khoản? Đăng ký</button>
        <span>Tài khoản Gia sư, Học sinh và Quản lý</span>
      </div>
      <img class="crab" src="${IMG}deco-crab.svg" alt="" />`,
    decos: "",
  });
  bindNav(root, go);
  try { const h = await api.health(); if (h.allow_register === false) $("#to-register", root).remove(); } catch { /* bỏ qua */ }
  const form = $("form", root);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const u = form.username.value.trim(), p = form.password.value;
    const errs = {};
    if (!u) errs.username = "Nhập tên đăng nhập";
    if (!p) errs.password = "Nhập mật khẩu";
    showErrors(form, errs);
    if (Object.keys(errs).length) return;
    const btn = $("button[type=submit]", form);
    btn.disabled = true; btn.textContent = "Đang đăng nhập…";
    try {
      onLoggedIn(await api.login(u, p));
    } catch (err) {
      btn.disabled = false; btn.textContent = "Đăng nhập";
      if (err.status === 401) showErrors(form, { username: "Thông tin đăng nhập chưa hợp lệ", password: "Thông tin đăng nhập chưa hợp lệ" });
      const box = $("#form-err", form); box.textContent = err.status === 401 ? "Sai tên đăng nhập hoặc mật khẩu." : err.message; box.classList.remove("hidden");
    }
  });
  form.username.focus();
}

export async function register(root, { go }) {
  frame(root, {
    tag1: "Bắt đầu với", tag2: "một cách học mới.",
    tag3: "Tạo tài khoản để luyện tập, xem tiến độ và nhận góp ý.",
    decos: `<img class="deco-a" src="${IMG}deco-starfish.svg" alt="" /><img class="deco-b" src="${IMG}deco-shell.svg" alt="" /><img class="deco-c" src="${IMG}deco-bubbles.svg" alt="" />`,
    card: `
      <h1>Tạo tài khoản TutorSim</h1>
      <p class="sub">Chọn vai trò và bắt đầu hành trình học tập.</p>
      <p class="sub2" style="font-size:16px">Thông tin có thể cập nhật sau khi đăng ký</p>
      <form class="auth-form" novalidate>
        ${field("name", "Tên hiển thị", "text", "Nhập tên hiển thị", 'maxlength="60" autocomplete="name"')}
        ${field("username", "Tên đăng nhập", "text", "Nhập tên đăng nhập (chữ thường không dấu, số)", 'autocomplete="username" autocapitalize="none" spellcheck="false"')}
        ${field("password", "Mật khẩu", "password", "Nhập mật khẩu (ít nhất 8 ký tự)", 'autocomplete="new-password"')}
        <div class="role-pick" role="radiogroup" aria-label="Vai trò">
          <b>Bạn đăng ký với vai trò nào?</b>
          <button type="button" class="role-btn" role="radio" aria-checked="false" data-role="tutor">Gia sư</button>
          <button type="button" class="role-btn" role="radio" aria-checked="false" data-role="student">Học sinh</button>
        </div>
        <span class="tf-error hidden" data-err="role"></span>
        <p class="form-error hidden" role="alert" id="form-err"></p>
        <div class="center"><button class="btn strong" type="submit">Tạo tài khoản</button></div>
      </form>
      <div class="auth-foot" style="margin-top:40px">
        <button class="link" type="button" data-to="login">Đã có tài khoản? Đăng nhập</button>
        <span>Đăng ký với thông tin chính xác để sử dụng TutorSim.</span>
      </div>`,
  });
  bindNav(root, go);
  let role = null;
  $$(".role-btn", root).forEach((b) => b.addEventListener("click", () => {
    role = b.dataset.role;
    $$(".role-btn", root).forEach((x) => x.setAttribute("aria-checked", String(x === b)));
  }));
  const form = $("form", root);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    // form.elements["name"]: không dùng form.name vì đó là thuộc tính name của chính thẻ <form>
    const name = form.elements["name"].value.trim(), username = form.elements["username"].value.trim().toLowerCase(), password = form.elements["password"].value;
    const errs = {};
    if (!name) errs.name = "Nhập tên hiển thị";
    if (!/^[a-z0-9_.]{3,32}$/.test(username)) errs.username = "3–32 ký tự: chữ thường không dấu, số, dấu chấm, gạch dưới";
    if (password.length < 8) errs.password = "Mật khẩu cần ít nhất 8 ký tự";
    if (!role) errs.role = "Chọn vai trò Gia sư hoặc Học sinh";
    showErrors(form, errs);
    if (Object.keys(errs).length) return;
    const btn = $("button[type=submit]", form);
    btn.disabled = true; btn.textContent = "Đang tạo…";
    try {
      onLoggedIn(await api.register(username, password, name, role));
    } catch (err) {
      btn.disabled = false; btn.textContent = "Tạo tài khoản";
      if (err.status === 409) showErrors(form, { username: err.message });
      const box = $("#form-err", form); box.textContent = err.message; box.classList.remove("hidden");
    }
  });
}

export async function forgot(root, { go }) {
  frame(root, {
    tag1: "Đồng hành cùng", tag2: "những người dạy học.",
    tag3: "Một không gian luyện giảng tập trung, được thiết kế để phản hồi rõ ràng.",
    card: `
      <div id="fg">
        <h1>Quên mật khẩu</h1>
        <p class="sub" style="font-size:14px">Nhập tên đăng nhập để gửi yêu cầu đặt lại mật khẩu.</p>
        <p class="sub" style="font-size:14px;margin-bottom:28px">Quản lý trung tâm sẽ đặt lại mật khẩu cho bạn.</p>
        <form class="auth-form" novalidate>
          ${field("username", "Tên đăng nhập", "text", "Nhập tên đăng nhập", 'autocomplete="username" autocapitalize="none"')}
          <p class="form-error hidden" role="alert" id="form-err"></p>
          <div><button class="btn strong" type="submit">Gửi yêu cầu</button></div>
        </form>
        <p style="margin:24px 0 0"><button class="link label-l" type="button" data-to="login" style="color:var(--on-surface)">Quay lại Đăng nhập</button></p>
        <p class="small muted" style="margin-top:48px">Yêu cầu được gửi tới quản lý trung tâm</p>
      </div>
      <img class="crab" src="${IMG}deco-crab.svg" alt="" />`,
  });
  bindNav(root, go);
  const form = $("form", root);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const u = form.username.value.trim();
    if (!u) return showErrors(form, { username: "Nhập tên đăng nhập" });
    const btn = $("button[type=submit]", form);
    btn.disabled = true;
    try {
      const r = await api.forgotPassword(u);
      $("#fg", root).innerHTML = `
        <h1>Đã nhận yêu cầu</h1>
        <p class="sub" style="font-size:14px">${esc(r.message)}</p>
        <p class="sub" style="font-size:14px">Liên hệ quản lý trung tâm để nhận mật khẩu mới.</p>
        <p style="margin:32px 0 0"><button class="btn strong" type="button" data-to="login">Trở về màn đăng nhập</button></p>`;
      bindNav(root, go);
    } catch (err) {
      btn.disabled = false;
      const box = $("#form-err", form); box.textContent = err.message; box.classList.remove("hidden");
    }
  });
}

function bindNav(root, go) {
  $$("[data-to]", root).forEach((b) => b.addEventListener("click", () => go(b.dataset.to)));
}
