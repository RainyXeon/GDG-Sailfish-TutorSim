// Học sinh: Trang chủ, Làm bài (danh sách đề + màn làm bài), Kết quả (theo Figma 02 • Học sinh).
import { api } from "../api.js";
import { $, $$, esc, IMG, icons, confirmDialog, toast, renderGeoGebra, fmtDateTime, fmtScore, wave, errorBox } from "../ui.js";
import { setLeaveGuard } from "../app.js";

const secTitle = (icon, title, extra = "") => `<div class="sec-title"><span class="sec-ic">${icon}</span><h2>${title}</h2>${extra}</div>`;
const mmss = (s) => `${String(Math.floor(s / 3600)).padStart(2, "0")}:${String(Math.floor((s % 3600) / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
const minText = (sec) => (sec < 60 ? `${sec} giây` : `${Math.round(sec / 60)} phút`);

function examRows(exams) {
  return exams.map((e) => `
    <div class="exam-row">
      <span class="doc">${icons.doc}</span>
      <div class="info"><b>${esc(e.title)}</b><span>${e.num_questions} câu &nbsp;&nbsp; ◷ ${e.time_limit_min} phút</span></div>
      <a class="btn violet" href="#/s/exam/${encodeURIComponent(e.id)}">Bắt đầu</a>
    </div>`).join("");
}

// ======================= TRANG CHỦ =======================
export async function home(main, { user }) {
  const [exams, sum] = await Promise.all([api.exams(), api.studentSummary(user.id)]);
  const p = sum.prediction;
  main.innerHTML = `
    <div class="card hero-wrap">
      <div class="hero">
        <span class="pastel" style="width:312px;height:301px;right:300px;top:-62px"></span>
        <div style="position:relative;z-index:1">
          <h1>Student Home</h1>
          <p>Xin chào ${esc(user.name)} · Theo dõi điểm dự kiến, đề luyện và lịch sử bài thi</p>
        </div>
        <img class="art" src="${IMG}hero-student.svg" alt="" />
      </div>
    </div>
    <div class="cols">
      <section class="card stack">
        ${secTitle(icons.bars, "Điểm Toán dự kiến")}
        ${p ? `
          <div class="empty predict">
            <span class="label-l muted">Khoảng điểm dự kiến</span>
            <div class="big">${fmtScore(p.low)} – ${fmtScore(p.high)}</div>
            <span>Giá trị giữa: <b>${fmtScore(p.mid)}</b> · ${esc(sum.note)}</span>
          </div>` : `
          <div class="empty">
            <div class="pics"><img src="${IMG}deco-shell.svg" alt="" width="84" /><span class="sec-ic" style="width:66px;height:66px">${icons.bars}</span><span style="width:84px"></span></div>
            <b>Chưa có dữ liệu</b><span>Hoàn thành ít nhất 2 đề để xem điểm dự kiến.</span>
          </div>`}
        ${secTitle(`<span style="color:var(--violet)">${icons.doc}</span>`, "Danh sách đề luyện")}
        <div class="stack">${examRows(exams)}</div>
        ${p ? "" : `<div class="notice violet"><span class="i">i</span><div>Cần hoàn thành ít nhất hai đề để có điểm dự kiến.</div></div>`}
        <div style="height:60px"></div>
        ${wave("sm")}
      </section>
      <section class="card stack">
        ${secTitle(`<span style="width:26px;height:26px;display:block">${icons.alertDoc}</span>`, "Lỗi sai thường gặp")}
        ${sum.top_misconceptions.length ? `<div class="stack">${sum.top_misconceptions.map((m) => `
            <div class="mis-row"><span class="ex"><i>!</i></span><div class="tx"><b>${esc(m.name)}</b><span>Mã lỗi ${esc(m.id)}</span></div><span class="cnt">${m.count} lần</span></div>`).join("")}</div>`
          : `<div class="empty"><div class="pics"><img src="${IMG}deco-crab.svg" alt="" width="84" style="transform:rotate(9deg)" />
              <span class="sec-ic" style="width:66px;height:66px"><span style="width:36px;height:36px;display:block">${icons.alertDoc}</span></span>
              <img src="${IMG}deco-starfish.svg" alt="" width="70" /></div>
              <b>Chưa có dữ liệu lỗi sai</b><span>Làm bài thi để hệ thống thống kê các lỗi sai thường gặp.</span></div>`}
        ${secTitle(`<img src="${IMG}ic-history.svg" alt="" width="45" height="45" />`, "Lịch sử bài thi").replace('<span class="sec-ic">', '<span class="sec-ic" style="background:none">')}
        ${sum.attempts.length ? `<div class="hist">${sum.attempts.slice(0, 6).map((a) => `
            <a class="hist-item" href="#/s/result/${a.attempt_id}"><div class="a"><b>${esc(a.exam_title)}</b><span>Đúng ${a.correct}/${a.total} câu</span></div>
              <span class="pill">${fmtScore(a.score10)}/10</span>
              <div class="c"><b>${fmtDateTime(a.created_at)}</b><span>Thời gian: ${minText(a.time_spent_sec)}</span></div></a>`).join("")}</div>`
          : `<div class="empty"><div class="pics"><img src="${IMG}shark-hi.svg" alt="" width="100" /><img src="${IMG}ic-history-empty.svg" alt="" width="60" /><img src="${IMG}shark-happy.svg" alt="" width="100" /></div>
              <b>Bạn chưa làm bài thi nào</b><span>Hãy bắt đầu làm đề luyện để xem lịch sử bài thi tại đây.</span></div>`}
      </section>
    </div>`;

  // Dialog chào mừng lần đầu (Figma 02 | Chào mừng)
  let seen = false;
  try { seen = localStorage.getItem("tutorsim_welcome_" + user.id) === "1"; } catch { /* bỏ qua */ }
  if (!seen && !sum.attempts.length) {
    try { localStorage.setItem("tutorsim_welcome_" + user.id, "1"); } catch { /* bỏ qua */ }
    const ok = await confirmDialog({ title: "Xin chào bạn!", message: "Chào mừng bạn đến với TutorSim.\nHãy cùng bắt đầu hành trình luyện tập hôm nay nhé!",
      ok: "Bắt đầu", cancel: "Để sau", pic: "shark-excited.svg" });
    if (ok) location.hash = "#/s/exams";
  }
}

// ======================= DANH SÁCH ĐỀ (Làm bài) =======================
export async function exams(main) {
  const list = await api.exams();
  const info = [["Cách làm bài", "Chọn đáp án và dùng danh sách câu hỏi để điều hướng"], ["Đếm thời gian", "Đồng hồ sẽ bắt đầu khi vào bài thi"],
    ["Nộp bài", "Cần xác nhận trước khi nộp kết quả"]];
  const m3 = (t, s, href) => `<${href ? `a href="${href}"` : "div"} class="m3card"><span class="mono">${esc(t.trim()[0] || "A")}</span>
      <span class="txt"><b>${esc(t)}</b><span>${esc(s)}</span></span><span class="ph" aria-hidden="true">
      <svg viewBox="0 0 40 40" fill="currentColor"><path d="M20 4l8 12H12z"/><circle cx="12" cy="28" r="7"/><rect x="22" y="21" width="14" height="14" rx="3"/></svg></span></${href ? "a" : "div"}>`;
  main.innerHTML = `
    <div class="card"><h1 class="headline-s" style="font-weight:700;font-size:28px">Làm bài</h1><p class="muted" style="margin:8px 0 0">Chọn đề luyện phù hợp trước khi bắt đầu.</p></div>
    <div class="card">
      <div class="two">
        <section class="card" style="box-shadow:none;padding:20px 16px 90px">
          <h2 class="title-l" style="font-weight:700">Danh sách đề luyện</h2>
          <p class="small muted" style="margin:8px 0 20px">Mỗi đề có thời gian và số câu hỏi riêng.</p>
          <div class="stack" style="gap:16px">${list.map((e) => m3(e.title, `${e.num_questions} câu · ${e.time_limit_min} phút`, `#/s/exam/${encodeURIComponent(e.id)}`)).join("")}</div>
          ${wave()}
        </section>
        <section class="card" style="box-shadow:none;padding:20px 16px 90px">
          <h2 class="title-l" style="font-weight:700">Thông tin trước khi thi</h2>
          <p class="small muted" style="margin:8px 0 20px">Xem hướng dẫn và chuẩn bị trước khi làm bài.</p>
          <div class="stack" style="gap:16px">${info.map(([t, s]) => m3(t, s)).join("")}</div>
          ${wave()}
        </section>
      </div>
      <div class="row" style="margin-top:20px;align-items:flex-end">
        ${list[0] ? `<a class="btn strong" href="#/s/exam/${encodeURIComponent(list[0].id)}">Bắt đầu ${esc(list[0].title.split("–")[0].trim().toLowerCase())}</a>` : ""}
        <img src="${IMG}shark-study.svg" alt="" width="110" /><img src="${IMG}shark-excited.svg" alt="" width="110" /><img src="${IMG}deco-seaweed.svg" alt="" width="50" />
      </div>
    </div>`;
}

// ======================= LÀM BÀI =======================
export async function exam(main, { params, go }) {
  const [ex, ticket] = await Promise.all([api.exam(params.id), api.startExam(params.id).catch(() => null)]);
  const qs = ex.questions;
  const st = { i: 0, answers: {}, flags: new Set(), left: ex.time_limit_min * 60, started: Date.now(), submitting: false, done: false };
  let timer = null;

  main.innerHTML = `
    <section class="card exam-head" style="padding:20px">
      <span class="docbig">${icons.doc.replace('viewBox="0 0 26 30"', 'viewBox="0 0 26 30" width="28" height="34"')}</span>
      <div><h1>${esc(ex.title)}</h1><div class="meta">${qs.length} câu hỏi &nbsp; | &nbsp; Thời gian làm bài: ${ex.time_limit_min} phút &nbsp; | &nbsp; Môn: Toán THPT</div></div>
      <div class="progress"><b id="prog-t"></b><div class="track"><div class="bar"><i id="prog-b" style="width:0"></i></div><span id="prog-p">0%</span></div></div>
      <div class="timer" id="timer"><img src="${IMG}ic-clock.svg" alt="" /><div><b id="clock" aria-live="off">--:--:--</b><span>Thời gian còn lại</span></div></div>
    </section>
    <div class="exam-cols">
      <section class="card">
        <h2 class="title-l" style="font-weight:700">Danh sách câu hỏi</h2>
        <div class="qlegend"><span><i style="background:var(--good)"></i>Đã làm</span><span><i style="background:#62a8ff"></i>Đang làm</span><span><i style="background:#eef2f7;border:1px solid #c9d3dd"></i>Chưa làm</span></div>
        <div class="qgrid" id="qgrid" role="list"></div>
        <hr style="border:0;border-top:2px solid #e7eef7;margin:24px 0 0" />
        <div class="geo-panel">
          <h3>Biểu diễn đồ thị</h3><p class="small muted" style="margin:4px 0 0">Đồ thị đồng bộ với câu hỏi hiện tại</p>
          <div class="geo-box" id="geo"></div>
          <div class="row"><b id="geo-cmd" class="label-l grow" style="color:#346da4"></b></div>
        </div>
      </section>
      <section class="card" style="display:flex;flex-direction:column">
        <div class="row"><span class="qbadge" id="qbadge"></span><span class="grow"></span>
          <button class="flag-btn" id="flag" aria-pressed="false">🔖 Đánh dấu câu hỏi</button></div>
        <p class="qtext" id="qtext"></p>
        <div id="answers" role="radiogroup" aria-labelledby="qtext"></div>
        <div class="row" style="margin-top:4px">
          <button class="btn outline" id="prev">← Câu trước</button><button class="btn outline" id="next">Câu sau →</button>
        </div>
        <div class="row" style="margin-top:auto;padding-top:24px;align-items:flex-end">
          <img src="${IMG}shark-study.svg" alt="" width="120" /><img src="${IMG}shark-excited.svg" alt="" width="120" /><img src="${IMG}deco-bubbles.svg" alt="" width="70" />
        </div>
        <div class="exam-foot">
          <div class="notice info grow" style="padding:8px 12px"><span class="i" style="background:#62a8ff">i</span><div>Bạn có thể thay đổi lựa chọn đáp án trước khi nộp bài.</div></div>
          <button class="btn strong" id="exit">Thoát bài thi</button>
          <button class="btn strong" id="submit">Nộp bài</button>
        </div>
        <div id="submit-err"></div>
      </section>
    </div>`;

  const answered = () => qs.filter((q) => st.answers[q.id]).length;
  function paintGrid() {
    $("#qgrid", main).innerHTML = qs.map((q, k) => `<button class="qbtn ${st.answers[q.id] ? "done" : ""} ${k === st.i ? "current" : ""} ${st.flags.has(q.id) ? "flag" : ""}"
      data-k="${k}" role="listitem" aria-label="Câu ${k + 1}${st.answers[q.id] ? ", đã làm" : ""}${k === st.i ? ", đang xem" : ""}">${k + 1}</button>`).join("");
    const n = answered(), pct = Math.round((n * 100) / qs.length);
    $("#prog-t", main).textContent = `Đã hoàn thành ${n}/${qs.length} câu`;
    $("#prog-b", main).style.width = pct + "%";
    $("#prog-p", main).textContent = pct + "%";
  }
  function paintQuestion() {
    const q = qs[st.i];
    $("#qbadge", main).textContent = `Câu ${st.i + 1}/${qs.length}`;
    $("#qtext", main).textContent = q.content;
    $("#answers", main).innerHTML = Object.entries(q.options).map(([k, v]) => `
      <button class="answer" role="radio" aria-checked="${st.answers[q.id] === k}" data-k="${k}"><span class="rd"></span><b>${k}.</b><span>${esc(v)}</span></button>`).join("");
    const f = $("#flag", main); f.setAttribute("aria-pressed", String(st.flags.has(q.id)));
    $("#prev", main).disabled = st.i === 0;
    $("#next", main).disabled = st.i === qs.length - 1;
    const cmds = q.geogebra_commands || [];
    $("#geo-cmd", main).textContent = cmds.length ? cmds.join(" · ") : "Câu hỏi này không yêu cầu hình biểu diễn";
    renderGeoGebra($("#geo", main), cmds, 290);
    paintGrid();
    MathJax.typesetPromise([main]).catch((err) => console.log("[MathJax / LaTeX] Typeset failed: " + err.message));
  }
  const goto = (k) => { st.i = Math.max(0, Math.min(qs.length - 1, k)); paintQuestion(); };
  $("#qgrid", main).addEventListener("click", (e) => { const b = e.target.closest("[data-k]"); if (b) goto(+b.dataset.k); });
  $("#answers", main).addEventListener("click", (e) => {
    const b = e.target.closest("[data-k]"); if (!b) return;
    st.answers[qs[st.i].id] = b.dataset.k; paintQuestion();
  });
  $("#prev", main).addEventListener("click", () => goto(st.i - 1));
  $("#next", main).addEventListener("click", () => goto(st.i + 1));
  $("#flag", main).addEventListener("click", () => { const id = qs[st.i].id; st.flags.has(id) ? st.flags.delete(id) : st.flags.add(id); paintQuestion(); });

  async function submit(auto = false) {
    if (st.submitting || st.done) return;
    st.submitting = true;
    const btn = $("#submit", main); btn.disabled = true; btn.textContent = "Đang chấm…";
    const answers = Object.fromEntries(qs.map((q) => [q.id, st.answers[q.id] || null]));
    const spent = Math.round((Date.now() - st.started) / 1000);
    try {
      const r = await api.submitAttempt(ex.id, answers, spent, ticket?.attempt_token);
      st.done = true; clearInterval(timer); setLeaveGuard(null);
      if (auto) await confirmDialog({ title: "Đã hết thời gian", message: "Bài thi đã tự động nộp.\nBạn có thể xem kết quả ngay bây giờ.", ok: "Xem kết quả", hideCancel: true, pic: "shark-cheer.svg" });
      go("s/result/" + r.attempt_id);
    } catch (e) {
      // Không mất bài: giữ nguyên đáp án, cho nộp lại
      st.submitting = false; btn.disabled = false; btn.textContent = "Nộp lại";
      $("#submit-err", main).innerHTML = `<div style="margin-top:12px">${errorBox(e, "Nộp lại")}</div>`;
      $("#submit-err [data-retry]", main)?.addEventListener("click", () => submit());
    }
  }
  $("#submit", main).addEventListener("click", async () => {
    const left = qs.length - answered();
    const ok = await confirmDialog({ title: "Xác nhận nộp bài",
      message: left ? `Bạn còn ${left} câu chưa làm.\nBạn có chắc muốn nộp bài?` : "Bạn đã làm hết các câu. Nộp bài ngay?",
      ok: "Nộp bài", cancel: "Tiếp tục làm", pic: "shark-study.svg" });
    if (ok) submit();
  });
  const askLeave = async () => st.done || await confirmDialog({ title: "Thoát bài thi?", message: "Thoát bài sẽ làm mất tiến trình hiện tại.\nBạn có chắc muốn thoát?",
    ok: "Thoát bài thi", cancel: "Ở lại", danger: true, pic: "shark-nam.svg" });
  $("#exit", main).addEventListener("click", async () => { if (await askLeave()) { st.done = true; go("s/exams"); } });
  setLeaveGuard(askLeave);
  const beforeUnload = (e) => { if (!st.done) { e.preventDefault(); e.returnValue = ""; } };
  window.addEventListener("beforeunload", beforeUnload);

  const tick = () => {
    const left = Math.max(0, ex.time_limit_min * 60 - Math.round((Date.now() - st.started) / 1000));
    $("#clock", main).textContent = mmss(left);
    $("#timer", main).classList.toggle("low", left <= 60);
    if (left <= 0) { clearInterval(timer); submit(true); }
  };
  timer = setInterval(tick, 1000);
  tick(); paintQuestion();
  return () => { clearInterval(timer); window.removeEventListener("beforeunload", beforeUnload); };
}

// ======================= KẾT QUẢ =======================
export async function results(main, { user }) {
  const sum = await api.studentSummary(user.id);
  main.innerHTML = `
    <div class="card"><h1 class="headline-s" style="font-weight:700;font-size:28px">Kết quả</h1>
      <p class="muted" style="margin:8px 0 0">Theo dõi điểm số và xem lại kiến thức cần cải thiện.</p></div>
    <section class="card" style="padding-bottom:100px">
      ${sum.attempts.length ? `
        <div class="row" style="margin-bottom:12px"><h2 class="title-l grow">Bài đã làm</h2><span class="label-m muted">${sum.attempts.length} bài</span></div>
        <div class="hist">${sum.attempts.map((a) => `
          <a class="hist-item" href="#/s/result/${a.attempt_id}"><div class="a"><b>${esc(a.exam_title)}</b><span>Đúng ${a.correct}/${a.total} câu · ${minText(a.time_spent_sec)}</span></div>
            <span class="pill">${fmtScore(a.score10)}/10</span><div class="c"><b>${fmtDateTime(a.created_at)}</b><span>Xem chi tiết →</span></div></a>`).join("")}</div>`
      : `<div class="empty" style="padding:40px"><div class="pics"><img src="${IMG}shark-hi.svg" alt="" width="120" /><img src="${IMG}deco-starfish.svg" alt="" width="70" /></div>
          <b>Chưa có bài thi hoàn thành</b><span>Hiện chưa có bài kiểm tra đã hoàn thành. Hoàn thành đề luyện đầu tiên để xem điểm số.</span>
          <a class="btn violet" href="#/s/exams" style="margin-top:12px">Đi đến Làm bài</a></div>`}
      ${wave()}
    </section>`;
}

export async function result(main, { params }) {
  const r = await api.attempt(params.id);
  const mis = [...new Map(r.results.filter((x) => x.misconception_id).map((x) => [x.misconception_id, x])).values()];
  const kind = (x) => (x.is_correct ? "good" : x.chosen ? "bad" : "blank");
  const label = { good: "Đúng", bad: "Sai", blank: "Bỏ trống" }, sym = { good: "✓", bad: "✕", blank: "–" };
  const show = { good: true, bad: true, blank: true };
  main.innerHTML = `
    <section class="card res-head">
      <div><div class="row"><span class="sec-ic" style="width:42px;height:42px">${icons.bars}</span><h1 class="title-l" style="font-weight:700">Kết quả bài thi</h1></div>
        <p class="muted" style="margin:8px 0 0 54px">${esc(r.exam_title)} · Xem điểm số, lỗi sai và lời giải chi tiết cho từng câu hỏi.</p>
        <div class="scorebig"><b>${fmtScore(r.score10)} / 10</b><span>Kết quả chung</span></div></div>
      <img src="${IMG}shark-excited.svg" alt="" width="150" />
      <div class="stack" style="align-items:flex-end">
        <div class="metrics">
          <div class="metric"><b>${r.correct} / ${r.total}</b><span>Số câu đúng</span></div>
          <div class="metric"><b>${minText(r.time_spent_sec)}</b><span>Thời gian làm bài</span></div>
          <div class="metric"><b>${r.num_misconceptions} lỗi</b><span>Lỗi nhận diện</span></div>
        </div>
        <span class="pill ${r.late ? "warn" : "good"}">${r.late ? "Nộp quá giờ" : "Hoàn thành"}</span>
      </div>
    </section>
    <div class="res-cols">
      <section class="card stack" style="padding-bottom:24px">
        <div class="row"><span class="sec-ic" style="width:42px;height:42px;background:var(--violet-bg-2)"><i style="width:24px;height:24px;border-radius:50%;background:var(--violet-2);color:#fff;display:grid;place-items:center;font:700 12px var(--font);font-style:normal">!</i></span>
          <h2 class="title-l" style="font-weight:700">Các lỗi sai được nhận diện</h2></div>
        ${mis.length ? mis.map((m) => `<div class="mis-row"><span class="ex"><i>!</i></span><div class="tx"><b>${esc(m.misconception_name || m.misconception_id)}</b>
            <span>${esc(m.misconception_description || "Mã lỗi " + m.misconception_id)}</span></div></div>`).join("")
          : `<div class="empty"><b>Không có lỗi sai nào được nhận diện</b><span>Các câu sai (nếu có) không gắn với lỗi sai điển hình.</span></div>`}
        <div class="explain" style="background:var(--surface-2)"><b style="color:var(--ink);font-size:16px;margin-bottom:8px">Phân loại trạng thái câu hỏi</b>
          <div class="row" style="gap:20px">${["good", "bad", "blank"].map((k) => `<span class="row" style="gap:8px"><span class="st-ic ${k}" style="flex-basis:28px;height:28px"><i>${sym[k]}</i></span>${label[k]}</span>`).join("")}</div></div>
        <div class="center"><img src="${IMG}shark-happy.svg" alt="" width="150" style="margin:16px auto" /></div>
        <a class="btn violet block" href="#/s/home" style="margin-top:auto">Trở về Student Home</a>
      </section>
      <section class="card stack">
        <div class="row"><span class="sec-ic" style="width:42px;height:42px"><b style="color:var(--violet-2)">≡</b></span>
          <h2 class="title-l grow" style="font-weight:700">Xem lại ${r.total} câu hỏi</h2>
          <div class="filters">${["good", "bad", "blank"].map((k) => `<button class="pill ${k}" aria-pressed="true" data-f="${k}">${label[k]}</button>`).join("")}</div></div>
        <div class="stack" id="reviews">${r.results.map((x, k) => {
          const t = kind(x);
          return `<div class="review ${t}" data-kind="${t}">
            <div class="review-head"><span class="st-ic ${t}"><i>${sym[t]}</i></span><span class="q">Câu ${k + 1}: ${esc(x.content || x.question_id)}</span><span class="pill ${t}">${label[t]}</span></div>
            <div class="ans-line"><b style="color:var(--${t === "good" ? "good" : t === "bad" ? "bad" : "blank"})">Đáp án bạn chọn:</b><span>${x.chosen ? `${x.chosen}. ${esc(x.chosen_text ?? "")}` : "Chưa chọn đáp án"}</span></div>
            <div class="ans-line"><b style="color:var(--good)">Đáp án đúng:</b><span>${x.correct_answer}. ${esc(x.correct_text ?? "")}</span></div>
            ${x.misconception_name ? `<div class="ans-line"><b style="color:var(--violet-2)">Lỗi sai:</b><span>${esc(x.misconception_name)}</span></div>` : ""}
            <div class="explain"><b>Giải thích:</b>${esc(x.explanation)}</div></div>`;
        }).join("")}</div>
      </section>
    </div>`;
  $$(".filters [data-f]", main).forEach((b) => b.addEventListener("click", () => {
    show[b.dataset.f] = !show[b.dataset.f];
    b.setAttribute("aria-pressed", String(show[b.dataset.f]));
    $$("#reviews .review", main).forEach((el) => el.classList.toggle("hidden", !show[el.dataset.kind]));
  }));
}