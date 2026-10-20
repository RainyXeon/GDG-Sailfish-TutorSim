// Quản lý trung tâm: Tổng quan, Gia sư, Kiến thức, Thống kê, Tài khoản (theo Figma 04 • Quản lý).
import { api } from "../api.js";
import { $, $$, esc, IMG, toast, formDialog, fmtDateTime, fmtMinutes, fmtVi, fmtScore, placeholderSvg, deco, wave } from "../ui.js";
import { changeName, changePassword, signOut, toggleTheme } from "../app.js";

const TOPIC = { ham_so: "Hàm số", oxyz: "Hình học Oxyz" };
const m3 = (title, sub, { href = "", current = false, letter } = {}) => {
  const tag = href ? "a" : "div";
  return `<${tag} class="m3card" ${href ? `href="${href}"` : ""} ${current ? 'aria-current="true"' : ""}>
    <span class="mono" aria-hidden="true">${esc(letter || (title || "A").trim()[0] || "A")}</span>
    <span class="txt"><b>${esc(title)}</b><span>${esc(sub)}</span></span><span class="ph" aria-hidden="true">${placeholderSvg}</span></${tag}>`;
};
const head = (title, sub, extra = "") => `
  <div class="mgr-title"><div><h1 class="headline-l">${title}</h1><p>${sub}</p></div>${extra}</div>`;
const panel = (title, sub, body, art = "") => `
  <section class="panel"><div class="panel-head"><div><h2>${title}</h2><p class="sub">${sub}</p></div>${art}</div>${body}</section>`;
const emptyBox = (t, s, pic = "shark-hi.svg") => `<div class="empty" style="padding:28px"><div class="pics"><img src="${IMG}${pic}" alt="" width="100" /></div><b>${t}</b><span>${s}</span></div>`;

// ======================= TỔNG QUAN =======================
export async function overview(main) {
  const o = await api.overview();
  const hasData = o.sessions_finished > 0 || o.attempts_count > 0;
  main.innerHTML = `
    ${head("Tổng quan quản lý", "Theo dõi hoạt động luyện giảng, hiệu suất gia sư và lỗi kiến thức cần cải thiện.")}
    <div class="mgr-body">
      <p class="label-l" style="color:var(--muted);margin:0">CHỈ SỐ TỔNG QUAN</p>
      <div class="metric-grid">
        ${m3("Buổi luyện", `${o.sessions_finished} phiên đã chấm`)}
        ${m3("Gia sư hoạt động", `${o.active_tutors} / ${o.tutors_count} tài khoản`)}
        ${m3("Điểm đánh giá", o.avg_total == null ? "Chưa có" : `${fmtVi(o.avg_total)} / 4 điểm`)}
        ${m3("Lỗi kiến thức", `${o.misconception_count} lượt ghi nhận`)}
      </div>
      ${hasData ? `<div class="two">
        ${panel("Hiệu suất gia sư", "Tổng hợp theo kết quả đánh giá",
          o.top_tutors.length ? `<div class="stack" style="gap:16px">${o.top_tutors.slice(0, 4).map((t) => m3(t.name, `${t.sessions_count} phiên  ·  ${fmtVi(t.avg_total)}/4`, { href: `#/m/tutors/${t.tutor_id}` })).join("")}</div>`
            : emptyBox("Chưa có buổi luyện được chấm", "Số liệu sẽ tự cập nhật khi bắt đầu có phiên luyện"),
          `<img src="${IMG}shark-excited.svg" alt="" width="80" /><img src="${IMG}deco-starfish.svg" alt="" width="82" style="transform:rotate(-12deg)" />`)}
        ${panel("Những hiểu nhầm phổ biến", "Ưu tiên các lỗi học sinh hay mắc",
          o.top_misconceptions.length ? `<div class="stack" style="gap:16px">${o.top_misconceptions.slice(0, 4).map((m) => m3(m.name, `${m.percent}% lượt ghi nhận · ${m.count} lượt`, { letter: m.id.slice(0, 2) === "OX" ? "O" : "H" })).join("")}</div>`
            : emptyBox("Chưa có dữ liệu bài làm", "Lỗi sẽ xuất hiện khi học sinh làm đề luyện", "deco-crab.svg"),
          `<img src="${IMG}deco-shell.svg" alt="" width="82" style="transform:rotate(11deg)" /><img src="${IMG}deco-bubbles.svg" alt="" width="70" />`)}
      </div>` : `
      <section class="panel" style="align-items:center;text-align:center;padding:48px">
        <div class="pics row" style="justify-content:center"><img src="${IMG}shark-hi.svg" alt="" width="140" /><img src="${IMG}deco-starfish.svg" alt="" width="80" /></div>
        <h2>Chưa có phiên luyện nào</h2><p class="sub">Hiện chưa có hoạt động luyện giảng nào để tổng hợp. Số liệu sẽ tự cập nhật khi bắt đầu có phiên luyện.</p>
      </section>`}
      <p class="muted" style="margin:0">Học sinh: ${o.students_count} tài khoản · ${o.attempts_count} bài làm · ${o.students_with_attempts} học sinh đã làm đề.</p>
    </div>`;
}

// ======================= GIA SƯ =======================
export async function tutors(main, { params, query, go }) {
  const q = query.q || "";
  const rows = await api.dashboard(q);
  const selId = params.id ? Number(params.id) : rows[0]?.tutor_id;
  main.innerHTML = `
    ${head("Quản lý gia sư", "Theo dõi danh sách, hoạt động và hiệu suất của từng gia sư.")}
    <div class="mgr-body">
      <div class="two">
        <section class="panel" style="padding-bottom:90px">
          <div class="panel-head" style="min-height:0"><div><h2>Danh sách gia sư</h2></div><img src="${IMG}deco-seaweed.svg" alt="" width="40" /></div>
          <form class="search" id="search" role="search">
            <label class="tf"><span>Tìm kiếm theo tên hoặc mã gia sư</span><input name="q" value="${esc(q)}" placeholder="Nhập tên hoặc mã gia sư" /></label>
            <button class="btn strong">Tìm</button></form>
          ${rows.length ? `<div class="stack" style="gap:14px">${rows.map((t) => m3(t.name, `${t.code} · ${t.status_label}`,
              { href: `#/m/tutors/${t.tutor_id}${q ? "?q=" + encodeURIComponent(q) : ""}`, current: t.tutor_id === selId })).join("")}</div>`
            : `<div class="empty"><b>Không tìm thấy gia sư</b><span>Không có gia sư nào phù hợp với điều kiện tìm kiếm.</span>
                <button class="btn outline" id="clear" style="margin-top:8px">Xóa bộ lọc</button></div>`}
          ${wave()}
        </section>
        <section class="panel" id="detail">${selId ? `<div class="spinner"></div>` : emptyBox("Chưa có gia sư", "Gia sư tự đăng ký sẽ xuất hiện tại đây.")}</section>
      </div>
    </div>`;
  $("#search", main).addEventListener("submit", (e) => {
    e.preventDefault();
    const v = new FormData(e.target).get("q").trim();
    go("m/tutors" + (v ? "?q=" + encodeURIComponent(v) : ""));
  });
  $("#clear", main)?.addEventListener("click", () => go("m/tutors"));
  if (!selId) return;
  const box = $("#detail", main);
  try {
    const [st, sessions, rubric] = await Promise.all([api.tutorStats(selId), api.tutorSessions(selId), api.rubric()]);
    box.innerHTML = `
      <div class="panel-head"><div><h2 style="font-weight:700">${esc(st.name)} · ${esc(st.code)}</h2>
        <p class="sub" style="font-size:13px">Toán THPT · ${st.active ? "Đang hoạt động" : "Tạm nghỉ"} · @${esc(st.username)}</p></div>
        <img src="${IMG}deco-cloud.svg" alt="" width="60" /><img src="${IMG}deco-coral.svg" alt="" width="50" /></div>
      <div class="kv">
        ${m3("Điểm đánh giá", st.avg_total == null ? "Chưa có" : `${fmtVi(st.avg_total)} / 4`)}
        ${m3("Số buổi luyện", `${st.sessions_count} phiên`)}
        ${m3("Tổng thời gian luyện", fmtMinutes(st.total_minutes))}
        ${m3("Tài khoản", st.active ? "Đang hoạt động" : "Tạm nghỉ (14 ngày chưa luyện)")}
      </div>
      <h3 class="title-m" style="margin:4px 0 0">Điểm trung bình theo tiêu chí</h3>
      ${Object.keys(st.avg_scores).length ? `<div class="stack" style="gap:10px">${rubric.map((c) => `<div class="hbar"><span>${esc(c.name)}<b>${fmtVi(st.avg_scores[c.key], 2)}/4</b></span>
          <div class="bar"><i style="width:${((st.avg_scores[c.key] || 0) / 4) * 100}%"></i></div></div>`).join("")}</div>` : `<p class="muted small">Chưa có buổi luyện được chấm.</p>`}
      <h3 class="title-m" style="margin:4px 0 0">Hoạt động gần đây</h3>
      ${sessions.length ? `<div class="hist">${sessions.slice(0, 6).map((s) => `<a class="hist-item" href="#/m/report/${s.session_id}">
          <div class="a"><b>${esc(s.chuyen_de_name || s.topic)}</b><span>Học sinh: ${esc(s.persona_name)} · ${esc(s.topic)}</span></div>
          <span class="pill">${fmtScore(s.total)}/4</span><div class="c"><b>${fmtDateTime(s.created_at)}</b><span>${fmtMinutes(s.duration_min)}</span></div></a>`).join("")}</div>`
        : `<p class="muted small">Gia sư chưa hoàn thành buổi luyện nào.</p>`}`;
  } catch (e) { box.innerHTML = `<div class="notice error"><span class="i">!</span><div>${esc(e.message)}</div></div>`; }
}

// ======================= KIẾN THỨC =======================
export async function knowledge(main) {
  const [topics, insights] = await Promise.all([api.topics(), api.insights()]);
  const rows = topics.filter((t) => t.dang_bai);
  const cdOf = (id) => (id.startsWith("OX") ? "Oxyz" : "Hàm số");
  main.innerHTML = `
    ${head("Quản lý kiến thức", "Theo dõi dạng bài luyện giảng và những hiểu nhầm kiến thức phổ biến.")}
    <div class="mgr-body">
      <div class="two">
        ${panel("Dạng bài Toán THPT", "Theo dõi tình trạng và mức độ luyện tập",
          rows.length ? `<div class="stack" style="gap:16px">${rows.slice(0, 8).map((t) => m3(t.label, `${t.sessions_count} phiên · ${t.student_misconception_count} lỗi ghi nhận`, { href: `#/m/knowledge/${t.chuyen_de}` })).join("")}</div>`
            : emptyBox("Chưa có dữ liệu phân tích", "Số liệu sẽ xuất hiện khi có phiên luyện hoặc bài làm."),
          `<img src="${IMG}shark-study.svg" alt="" width="64" /><img src="${IMG}deco-crab.svg" alt="" width="64" />`)}
        ${panel("Lỗi kiến thức thường gặp", "Những lỗi học sinh mắc nhiều nhất khi làm đề",
          insights.length ? `<div class="stack" style="gap:16px">${insights.slice(0, 8).map((m) => m3(m.name, `${m.count} lượt · Chủ đề ${cdOf(m.id)}`, { letter: m.id.slice(0, 2) === "OX" ? "O" : "H" })).join("")}</div>`
            : emptyBox("Chưa có dữ liệu lỗi sai", "Lỗi sẽ xuất hiện khi học sinh làm đề luyện.", "deco-starfish.svg"),
          `<img src="${IMG}deco-starfish.svg" alt="" width="60" /><img src="${IMG}deco-shell.svg" alt="" width="56" />`)}
      </div>
      <div class="row"><a class="btn strong" href="#/m/knowledge/ham_so">Xem chi tiết Hàm số</a><a class="btn strong" href="#/m/knowledge/oxyz">Xem chi tiết Hình học Oxyz</a></div>
    </div>`;
}

export async function knowledgeDetail(main, { params }) {
  const cd = params.cd;
  const rows = await api.topics(cd);
  const total = rows.find((r) => !r.dang_bai) || { sessions_count: 0, student_misconception_count: 0, avg_total: null, tutors_count: 0, student_top_misconceptions: [], practiced_misconceptions: [] };
  const name = TOPIC[cd] || cd;
  main.innerHTML = `
    ${head(`Chi tiết kiến thức · ${esc(name)}`, `Phân tích những lỗi học sinh hay mắc và các buổi luyện giảng trong chủ đề ${esc(name)}.`,
      `<div class="row">${Object.entries(TOPIC).map(([k, v]) => `<a class="btn ${k === cd ? "tonal" : "outline"}" href="#/m/knowledge/${k}">${v}</a>`).join("")}</div>`)}
    <div class="mgr-body">
      <div class="two">
        ${panel("Tổng quan chủ đề", "Số liệu thật từ backend", `<div class="stack" style="gap:16px">
          ${m3("Phiên luyện đã thực hiện", `${total.sessions_count} phiên`)}${m3("Lỗi sai được phát hiện", `${total.student_misconception_count} lượt`)}
          ${m3("Điểm đánh giá trung bình", total.avg_total == null ? "Chưa có" : `${fmtVi(total.avg_total)} / 4`)}${m3("Gia sư tham gia", `${total.tutors_count} người`)}</div>`,
          `<img src="${IMG}deco-seaweed.svg" alt="" width="36" /><img src="${IMG}deco-cloud.svg" alt="" width="60" />`)}
        ${panel("Các lỗi cần chú ý", "Lỗi học sinh hay mắc trong chủ đề này", (total.student_top_misconceptions.length
            ? `<div class="stack" style="gap:16px">${total.student_top_misconceptions.map((m) => m3(m.name, `${m.count} lượt · ${m.id}`)).join("")}</div>`
            : emptyBox("Chưa có lỗi được ghi nhận", "Học sinh chưa làm đề thuộc chủ đề này.", "shark-study.svg"))
          + `<h3 class="title-m" style="margin:8px 0 0">Theo dạng bài</h3>` + (rows.filter((r) => r.dang_bai).length
            ? `<div class="stack" style="gap:10px">${rows.filter((r) => r.dang_bai).map((r) => `<div class="hbar"><span>${esc(r.dang_bai)}<b>${r.sessions_count} phiên · ${r.student_misconception_count} lỗi</b></span>
                <div class="bar"><i style="width:${Math.min(100, (r.sessions_count + r.student_misconception_count) * 100 / Math.max(1, total.sessions_count + total.student_misconception_count))}%"></i></div></div>`).join("")}</div>`
            : `<p class="muted small">Chưa có dữ liệu.</p>`),
          `<img src="${IMG}deco-bubbles.svg" alt="" width="50" />`)}
      </div>
      <div><a class="btn strong" href="#/m/knowledge">Quay lại danh sách</a></div>
    </div>`;
}

// ======================= THỐNG KÊ =======================
export async function stats(main) {
  const [o, topics] = await Promise.all([api.overview(), api.topics()]);
  const rows = topics.filter((t) => t.dang_bai).sort((a, b) => b.sessions_count - a.sessions_count);
  const max = Math.max(1, ...rows.map((r) => r.sessions_count));
  main.innerHTML = `
    ${head("Thống kê & báo cáo", "Phân tích hiệu suất luyện giảng và các dạng bài thường gặp lỗi.")}
    <div class="mgr-body">
      <div class="two">
        ${panel("Hiệu suất luyện giảng", "Số liệu tổng hợp từ backend", `<div class="stack" style="gap:16px">
          ${m3("Tổng phiên luyện", `${o.sessions_total} phiên`)}${m3("Điểm đánh giá trung bình", o.avg_total == null ? "Chưa có" : `${fmtVi(o.avg_total)} / 4`)}
          ${m3("Gia sư có hoạt động", `${o.active_tutors} gia sư`)}${m3("Phiên đã hoàn thành", `${o.sessions_finished} / ${o.sessions_total} phiên`)}</div>`)}
        ${panel("Thống kê theo dạng bài", "Phân bố phiên luyện của gia sư", rows.length
            ? `<p class="title-m" style="margin:0">Số phiên luyện theo dạng bài</p><div class="stack" style="gap:14px">${rows.slice(0, 8).map((r) => `<div class="hbar"><span>${esc(r.label)}<b>${r.sessions_count}</b></span>
                <div class="bar"><i style="width:${(r.sessions_count / max) * 100}%"></i></div></div>`).join("")}</div>`
            : emptyBox("Thống kê sẽ xuất hiện khi có hoạt động luyện giảng.", ""),
          `<img src="${IMG}shark-excited.svg" alt="" width="80" />`)}
      </div>
      <div class="row"><a class="btn strong" href="#/m/stats/ham_so">Xem theo chủ đề</a></div>
    </div>`;
}

export async function statsTopic(main, { params }) {
  const cd = params.cd;
  const [rows, all] = await Promise.all([api.topics(cd), api.topics()]);
  const total = rows.find((r) => !r.dang_bai) || { sessions_count: 0, avg_total: null, tutors_count: 0, student_misconception_count: 0 };
  const sub = rows.filter((r) => r.dang_bai && r.avg_total != null);
  const compare = all.filter((r) => !r.dang_bai);
  main.innerHTML = `
    ${head("Thống kê theo chủ đề", "Đối chiếu hiệu suất giảng dạy giữa các chủ đề Toán THPT.",
      `<div class="row">${Object.entries(TOPIC).map(([k, v]) => `<a class="btn ${k === cd ? "tonal" : "outline"}" href="#/m/stats/${k}">${v}</a>`).join("")}</div>`)}
    <div class="mgr-body">
      <div class="two">
        ${panel(`Thống kê ${esc(TOPIC[cd] || cd)}`, "Kết quả tổng hợp", `<div class="stack" style="gap:16px">
          ${m3("Tổng số phiên luyện", `${total.sessions_count} phiên`)}${m3("Mức đánh giá trung bình", total.avg_total == null ? "Chưa có" : `${fmtVi(total.avg_total)} / 4`)}
          ${m3("Gia sư luyện tập", `${total.tutors_count} tài khoản`)}${m3("Lỗi kiến thức phổ biến", `${total.student_misconception_count} lượt`)}</div>`)}
        ${panel("So sánh", "Điểm đánh giá trung bình (thang 4)", `
          <p class="title-m" style="margin:0">Giữa các chuyên đề</p>
          ${compare.length ? `<div class="stack" style="gap:12px">${compare.map((r) => `<div class="hbar"><span>${esc(r.label)}<b>${fmtVi(r.avg_total)}/4</b></span><div class="bar"><i style="width:${((r.avg_total || 0) / 4) * 100}%"></i></div></div>`).join("")}</div>` : `<p class="muted small">Chưa có dữ liệu.</p>`}
          <p class="title-m" style="margin:8px 0 0">Theo dạng bài trong ${esc(TOPIC[cd] || cd)}</p>
          ${sub.length ? `<div class="stack" style="gap:12px">${sub.map((r) => `<div class="hbar"><span>${esc(r.dang_bai)}<b>${fmtVi(r.avg_total)}/4</b></span><div class="bar"><i style="width:${((r.avg_total || 0) / 4) * 100}%"></i></div></div>`).join("")}</div>` : `<p class="muted small">Chưa có dữ liệu.</p>`}`,
          `<img src="${IMG}shark-excited.svg" alt="" width="80" />`)}
      </div>
      <div><a class="btn strong" href="#/m/stats">Quay lại thống kê</a></div>
    </div>`;
}

// ======================= TÀI KHOẢN =======================
export async function account(main, { user, go }) {
  const reqs = await api.resetRequests();
  const opt = (t, s, a) => `<button class="m3card" data-a="${a}"><span class="mono">${t[0]}</span><span class="txt"><b>${t}</b><span>${s}</span></span><span class="ph">${placeholderSvg}</span></button>`;
  main.innerHTML = `
    ${head("Cài đặt tài khoản", "Xem thông tin người quản lý, các tùy chọn sử dụng TutorSim và yêu cầu đặt lại mật khẩu.")}
    <div class="mgr-body">
      <div class="two">
        ${panel("Thông tin cá nhân", "Quản lý thông tin tài khoản", `<div class="stack" style="gap:16px">
          ${m3("Vai trò", "Quản lý hệ thống")}${m3("Tên đăng nhập", user.username)}${m3("Tên hiển thị", user.name)}${m3("Mã tài khoản", user.code)}</div>`,
          `<img src="${IMG}shark-admin.svg" alt="" width="56" /><img src="${IMG}deco-cloud.svg" alt="" width="56" />`)}
        ${panel("Tùy chọn sử dụng", "Thiết lập theo nhu cầu", `<div class="stack" style="gap:16px">
          ${opt("Chế độ giao diện", "Sáng / Tối – bấm để chuyển", "theme")}${opt("Đổi tên hiển thị", "Cập nhật tên hiển thị", "name")}
          ${opt("Bảo mật tài khoản", "Thay đổi mật khẩu", "pw")}${opt("Phiên đăng nhập", "Đăng xuất an toàn", "logout")}</div>`,
          `<img src="${IMG}deco-crab.svg" alt="" width="60" />`)}
      </div>
      ${panel("Yêu cầu đặt lại mật khẩu", "Gia sư / học sinh bấm “Quên mật khẩu” sẽ xuất hiện ở đây. Đặt mật khẩu mới rồi báo cho họ.",
        reqs.length ? `<table class="table"><thead><tr><th>Tài khoản</th><th>Vai trò</th><th>Thời điểm</th><th></th></tr></thead><tbody>
          ${reqs.map((r) => `<tr><td><b>${esc(r.name)}</b><br/><span class="small muted">@${esc(r.username)} · ${esc(r.code)}</span></td>
            <td>${r.role === "tutor" ? "Gia sư" : "Học sinh"}</td><td>${fmtDateTime(r.created_at)}</td>
            <td style="text-align:right"><button class="btn tonal" data-reset="${r.user_id}" data-name="${esc(r.name)}">Đặt mật khẩu mới</button></td></tr>`).join("")}</tbody></table>`
          : `<p class="muted" style="margin:0">Không có yêu cầu nào đang chờ.</p>`)}
    </div>`;
  $$("[data-a]", main).forEach((b) => b.addEventListener("click", () => {
    const a = b.dataset.a;
    if (a === "theme") toggleTheme();
    if (a === "name") changeName();
    if (a === "pw") changePassword();
    if (a === "logout") signOut();
  }));
  $$("[data-reset]", main).forEach((b) => b.addEventListener("click", () => formDialog({
    title: `Đặt mật khẩu mới cho ${b.dataset.name}`, ok: "Đặt mật khẩu",
    fields: [{ name: "pw", label: "Mật khẩu mới (ít nhất 8 ký tự)", type: "text" }],
    onSubmit: async ({ pw }) => {
      if (pw.length < 8) return "Mật khẩu cần ít nhất 8 ký tự.";
      try { await api.resetPassword(b.dataset.reset, pw); toast("Đã đặt mật khẩu mới. Hãy báo cho người dùng."); go("m/account"); return null; } catch (e) { return e.message; }
    },
  })));
}
