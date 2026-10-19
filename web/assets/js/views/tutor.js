// Gia sư: Trang chủ (chọn chuyên đề + tính cách), Luyện tập (chat với Nam), Báo cáo (theo Figma 03 • Gia sư).
import { api } from "../api.js";
import { $, $$, esc, IMG, confirmDialog, toast, renderGeoGebra, fmtDateTime, fmtMinutes, fmtScore, wave, deco, errorBox } from "../ui.js";

const TOPICS = {
  ham_so: ["Hàm số", "Đơn điệu, cực trị, GTLN – GTNN, tiệm cận, bảng biến thiên."],
  oxyz: ["Hình học Oxyz", "Vectơ, mặt phẳng, đường thẳng, mặt cầu, khoảng cách, góc."],
};
// Mô tả ngắn hiển thị trên thẻ (tên lấy từ backend /api/personas)
const PERSONA_HINT = {
  thu_dong: "Ít hỏi lại, trả lời ngắn, cần được gợi mở từng bước.",
  hay_cai: "Bảo vệ cách làm sai, cần lập luận và phản ví dụ thuyết phục.",
  mat_goc: "Hổng kiến thức nền, cần giải thích lại từ khái niệm cơ bản.",
  nhanh_nhung_au: "Làm nhanh nhưng hay sai dấu, tính toán hoặc bỏ sót trường hợp.",
};
const topicName = (cd) => TOPICS[cd]?.[0] || cd;

function histItem(s) {
  const unfinished = s.status !== "finished";
  const href = unfinished ? `#/t/practice/${s.session_id}` : `#/t/report/${s.session_id}`;
  return `<a class="hist-item" href="${href}">
    <div class="a"><b>${esc(s.chuyen_de_name || topicName(s.chuyen_de) || s.topic)}</b><span>Học sinh: ${esc(s.persona_name || "–")} · ${esc(s.topic)}</span></div>
    ${unfinished ? `<span class="pill warn">${s.status === "abandoned" ? "Đã bỏ" : "Đang dở"}</span>` : `<span class="pill">${fmtScore(s.total)}/4</span>`}
    <div class="c"><b>${fmtDateTime(s.created_at)}</b><span>${unfinished ? (s.status === "abandoned" ? "Không chấm" : "Làm tiếp →") : "Thời lượng: " + fmtMinutes(s.duration_min)}</span></div></a>`;
}

// ======================= TRANG CHỦ =======================
export async function home(main, { user, go }) {
  const [stats, personas, sessions] = await Promise.all([api.tutorStats(user.id), api.personas(), api.tutorSessions(user.id, true)]);
  const shown = sessions.filter((s) => s.status !== "abandoned").slice(0, 5);
  const sel = { cd: null, persona: null };
  main.innerHTML = `
    <section class="card page-head">
      <span class="avatar" style="width:72px;height:72px"><img src="${IMG}shark-tutor.svg" alt="" /></span>
      <div class="who">
        <p class="headline-s">Xin chào, ${esc(user.name)}</p>
        <p class="body-l muted">Gia sư môn Toán THPT · Mã gia sư: ${esc(user.code)}</p>
        <p class="label-l muted" style="font-weight:400">Chọn chuyên đề và tính cách học sinh ảo để bắt đầu một buổi luyện giảng mới.</p>
      </div>
      <img src="${IMG}shark-wave.svg" alt="" width="110" height="86" />
      <div class="stats">
        <div class="stat"><b>${stats.sessions_count}</b><span>Buổi đã luyện</span></div>
        <div class="stat"><b>${stats.avg_total == null ? "–" : fmtScore(stats.avg_total) + "/4"}</b><span>Điểm trung bình</span></div>
        <div class="stat"><b>${fmtMinutes(stats.total_minutes)}</b><span>Tổng thời gian</span></div>
      </div>
    </section>
    <div class="cols">
      <section class="card stack" style="gap:16px">
        <div><h1 class="title-l">Thiết lập buổi luyện mới</h1>
          <p class="label-l muted" style="font-weight:400;margin:4px 0 0">Học sinh ảo Nam sẽ đóng vai theo chuyên đề và tính cách bạn chọn.</p></div>
        <p class="step-title">1. Chọn chuyên đề</p>
        <div class="opt-grid" role="radiogroup" aria-label="Chuyên đề">
          ${Object.entries(TOPICS).map(([k, [t, d]]) => `<button class="opt" role="radio" aria-checked="false" data-cd="${k}"><span class="radio"></span>
            <span><span class="t">${t}</span><br/><span class="d">${d}</span></span></button>`).join("")}
        </div>
        <p class="step-title">2. Chọn tính cách học sinh ảo (không chọn: ngẫu nhiên)</p>
        <div class="opt-grid" role="radiogroup" aria-label="Tính cách học sinh ảo">
          ${personas.map((p) => `<button class="opt persona" role="radio" aria-checked="false" data-p="${p.id}"><span class="radio"></span>
            <span class="pic"><img src="${IMG}persona-${p.id}.svg" alt="" onerror="this.src='${IMG}shark-nam.svg'" /></span>
            <span><span class="t">${esc(p.ten)}</span><br/><span class="d">${esc(PERSONA_HINT[p.id] || p.mo_ta)}</span></span></button>`).join("")}
        </div>
        <p class="small muted" style="margin:-4px 0 0">Bấm lại vào tính cách đang chọn để bỏ chọn (Nam sẽ có tính cách ngẫu nhiên).</p>
        <div id="start-err"></div>
        <div class="summary-bar">
          <div class="grow"><div class="label-m">Lựa chọn hiện tại</div><div class="title-m" id="sum"></div></div>
          <button class="btn lg" id="start" disabled>Bắt đầu buổi luyện</button>
        </div>
        ${deco("deco-cloud.svg", "left:30%;bottom:90px;opacity:.9")}
      </section>
      <section class="card stack" style="padding-bottom:110px">
        <div class="row"><h2 class="title-l grow">Lịch sử luyện tập</h2><span class="label-m muted">${shown.length ? Math.min(5, shown.length) + " buổi gần nhất" : ""}</span></div>
        ${shown.length ? `<div class="hist">${shown.map(histItem).join("")}</div>
            ${sessions.length > 5 ? `<a class="link label-l" href="#/t/reports">Xem tất cả buổi luyện →</a>` : ""}`
          : `<div class="empty"><div class="pics"><img src="${IMG}shark-hi.svg" alt="" width="110" /><img src="${IMG}deco-bubbles.svg" alt="" width="60" /></div>
              <b>Chưa có buổi luyện nào</b><span>Lịch sử luyện tập, điểm số và thời gian sẽ xuất hiện tại đây sau khi bạn hoàn thành buổi luyện đầu tiên.</span></div>`}
        <div class="deco-row"><img src="${IMG}deco-bubbles.svg" alt="" width="70" /><img src="${IMG}deco-seaweed.svg" alt="" width="60" /></div>
        ${wave()}
      </section>
    </div>`;

  const paint = () => {
    $$("[data-cd]", main).forEach((b) => b.setAttribute("aria-checked", String(b.dataset.cd === sel.cd)));
    $$("[data-p]", main).forEach((b) => b.setAttribute("aria-checked", String(b.dataset.p === sel.persona)));
    const pName = personas.find((p) => p.id === sel.persona)?.ten;
    $("#sum", main).textContent = `${sel.cd ? topicName(sel.cd) : "Chưa chọn chuyên đề"} · ${pName ? "Học sinh Nam – " + pName : "Tính cách ngẫu nhiên"}`;
    $("#start", main).disabled = !sel.cd;
  };
  $$("[data-cd]", main).forEach((b) => b.addEventListener("click", () => { sel.cd = b.dataset.cd; paint(); }));
  $$("[data-p]", main).forEach((b) => b.addEventListener("click", () => { sel.persona = sel.persona === b.dataset.p ? null : b.dataset.p; paint(); }));
  $("#start", main).addEventListener("click", async () => {
    const btn = $("#start", main);
    btn.disabled = true; btn.textContent = "Nam đang chuẩn bị bài…";
    $("#start-err", main).innerHTML = "";
    try {
      const s = await api.startSession(sel.cd, sel.persona);
      if (s.persona_random) toast(`Tính cách ngẫu nhiên của Nam: ${s.persona_name}`);
      go("t/practice/" + s.session_id);
    } catch (e) {
      btn.disabled = false; btn.textContent = "Bắt đầu buổi luyện";
      $("#start-err", main).innerHTML = errorBox(e, "");
    }
  });
  paint();
}

// ======================= LUYỆN TẬP: danh sách buổi dở =======================
export async function practiceIndex(main, { user }) {
  const sessions = (await api.tutorSessions(user.id, true)).filter((s) => s.status === "in_progress");
  main.innerHTML = `
    <section class="card"><h1 class="headline-s">Luyện tập</h1><p class="muted" style="margin:6px 0 0">Tiếp tục buổi luyện đang dở hoặc bắt đầu buổi mới ở Trang chủ.</p></section>
    <section class="card stack" style="padding-bottom:110px">
      ${sessions.length ? `<h2 class="title-l">Buổi luyện đang dở</h2><div class="hist">${sessions.map(histItem).join("")}</div>`
        : `<div class="empty" style="padding:40px"><div class="pics"><img src="${IMG}shark-wave.svg" alt="" width="110" /></div>
            <b>Không có buổi luyện nào đang dở</b><span>Chọn chuyên đề và tính cách học sinh ảo ở Trang chủ để bắt đầu.</span>
            <a class="btn" href="#/t/home" style="margin-top:12px">Thiết lập buổi luyện mới</a></div>`}
      ${wave()}
    </section>`;
}

// ======================= LUYỆN TẬP: chat với Nam =======================
export async function practice(main, { params, go }) {
  const id = params.id;
  const s = await api.session(id);
  if (s.status === "finished") return go("t/report/" + id);
  const lines = String(s.student_solution || "").split(/\n|(?<=\.)\s+(?=Vậy)/).filter(Boolean);
  let collapsed = false, sending = false, finishing = false, lastFailed = null;

  main.innerHTML = `
    <section class="card pad-sm stack" style="gap:16px">
      <div class="row">
        <div class="grow"><h1 class="title-l">Buổi luyện · ${esc(topicName(s.chuyen_de))}</h1>
          <div class="row" style="gap:8px;margin-top:8px"><span class="chip">Học sinh ảo: ${esc(s.student_name)}</span><span class="chip">Tính cách: ${esc(s.persona_name)}</span>
          <span class="chip">${esc(s.topic)}</span></div></div>
        ${s.status === "abandoned" ? `<span class="pill warn">Buổi này đã bị bỏ</span><a class="btn outline" href="#/t/home">Về trang chủ</a>` : `
        <button class="btn outline danger" id="abandon">Bỏ buổi luyện</button>
        <button class="btn" id="finish">Kết thúc buổi luyện</button>`}
      </div>
      <div class="problem-row">
        <div class="problem"><p class="overline">Đề bài</p><p class="body-l" style="margin-top:8px">${esc(s.problem)}</p>${wave("sm")}</div>
        <div class="solution"><p class="overline">Bài giải của ${esc(s.student_name)}</p>
          ${lines.map((l, k) => `<p class="line ${k === lines.length - 1 && lines.length > 1 ? "wrong" : ""}">${esc(l)}</p>`).join("")}</div>
      </div>
    </section>
    <div class="practice-cols" id="pcols">
      <section class="card chat">
        <div class="chat-head">
          <span class="avatar" style="width:40px;height:40px"><img src="${IMG}shark-nam.svg" alt="" /></span>
          <div class="grow"><b class="title-m">${esc(s.student_name)}</b><div class="label-m muted">Học sinh ảo · Tính cách ${esc(String(s.persona_name).toLowerCase())}</div></div>
          <div class="legend"><span><i style="background:var(--primary)"></i>Gia sư</span><span><i style="background:#d9dde3"></i>${esc(s.student_name)}</span></div>
        </div>
        <div class="chat-log" id="log" aria-live="polite"></div>
        <div id="banner"></div>
        ${s.status === "abandoned" ? "" : `
        <form class="composer" id="composer">
          <label class="tf"><span>Tin nhắn</span><textarea id="draft" rows="1" placeholder="Nhập tin nhắn cho ${esc(s.student_name)}…" aria-label="Tin nhắn cho ${esc(s.student_name)}"></textarea></label>
          <button class="btn" type="submit" id="send">Gửi</button>
        </form>`}
      </section>
      <section class="card geo-card" id="geocard">
        <div class="row"><div class="grow"><b class="title-m">Minh họa GeoGebra</b><div class="label-m muted">${esc(s.geogebra_commands.join(" · ") || "Bài này chưa có hình minh họa")}</div></div>
          <button class="btn tonal" id="collapse">Thu gọn</button></div>
        <div class="geo-box" id="geo"></div>
        ${wave()}
      </section>
    </div>`;

  const log = $("#log", main);
  const avatar = (me) => `<span class="avatar" style="width:32px;height:32px"><img src="${IMG}${me ? "shark-tutor.svg" : "shark-nam.svg"}" alt="" /></span>`;
  const bubble = (role, text, warnings = []) => {
    const me = role === "tutor";
    return `<div class="msg ${me ? "me" : ""}">${me ? "" : avatar(false)}
      <div class="body"><span class="who">${me ? "Bạn (Gia sư)" : esc(s.student_name) + " · Học sinh ảo"}</span><div class="bubble">${esc(text)}</div>
        ${warnings.map((w) => `<span class="warn">Kiểm tra lại: ${esc(w)}</span>`).join("")}</div>${me ? avatar(true) : ""}</div>`;
  };
  const scroll = () => { log.scrollTop = log.scrollHeight; };
  log.innerHTML = bubble("student", "Em làm xong rồi ạ. Thầy/cô xem giúp em bài này nhé.") + s.messages.map((m) => bubble(m.role, m.content, m.math_warnings)).join("");
  scroll();
  if (s.student_understood) showUnderstood();

  function showUnderstood() {
    $("#banner", main).innerHTML = `<div class="chat-banner ok"><img src="${IMG}shark-cheer.svg" alt="" width="40" /><p><b>${esc(s.student_name)} đã hiểu bài!</b>
      ${esc(s.student_name)} đã tự sửa lại kết luận. Bạn có thể kết thúc buổi luyện để xem báo cáo đánh giá.</p></div>`;
  }
  function showError(e, retry) {
    $("#banner", main).innerHTML = `<div class="chat-banner error"><img src="${IMG}shark-nam.svg" alt="" width="40" style="filter:grayscale(.4)" />
      <p><b>${e.status === 503 || e.status === 0 ? "Mất kết nối với học sinh ảo" : "Có lỗi xảy ra"}</b>${esc(e.message)}${e.retryAfter ? ` (thử lại sau khoảng ${e.retryAfter} giây)` : ""}</p>
      ${retry ? `<button class="btn outline danger" id="retry">Thử lại</button>` : ""}</div>`;
    $("#retry", main)?.addEventListener("click", retry);
  }

  async function send(text) {
    if (sending || !text) return;
    sending = true;
    $("#send", main).disabled = true;
    $("#banner", main).innerHTML = "";
    if (lastFailed) { lastFailed.remove(); lastFailed = null; }
    log.insertAdjacentHTML("beforeend", bubble("tutor", text));
    const mine = log.lastElementChild;
    log.insertAdjacentHTML("beforeend", `<div class="typing" id="typing">${avatar(false)}<img src="${IMG}typing.svg" alt="" />${esc(s.student_name)} đang trả lời…</div>`);
    scroll();
    try {
      const r = await api.sendMessage(id, text);
      $("#typing", main)?.remove();
      if (r.math_warnings?.length) mine.querySelector(".body").insertAdjacentHTML("beforeend", r.math_warnings.map((w) => `<span class="warn">Kiểm tra lại: ${esc(w)}</span>`).join(""));
      log.insertAdjacentHTML("beforeend", bubble("student", r.student_reply));
      if (r.status === "student_understood") showUnderstood();
    } catch (e) {
      $("#typing", main)?.remove();
      mine.classList.add("failed");
      mine.querySelector(".body").insertAdjacentHTML("beforeend", `<span class="fail">● Chưa gửi được</span>`);
      lastFailed = mine;
      showError(e, () => send(text));
      if (e.status === 409) { showError(e, null); }
    } finally {
      sending = false; $("#send", main) && ($("#send", main).disabled = false); scroll();
    }
  }

  const form = $("#composer", main);
  if (form) {
    const draft = $("#draft", main);
    form.addEventListener("submit", (e) => { e.preventDefault(); const t = draft.value.trim(); if (!t) return; draft.value = ""; send(t); });
    draft.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
    draft.focus();
    $("#abandon", main).addEventListener("click", async () => {
      const ok = await confirmDialog({ title: "Bỏ buổi luyện?", message: `Hội thoại với ${s.student_name} sẽ không được chấm và không có báo cáo cho buổi này. Bạn có chắc muốn bỏ?`,
        ok: "Bỏ buổi", cancel: "Ở lại", danger: true, pic: "shark-nam.svg" });
      if (!ok) return;
      try { await api.abandonSession(id); toast("Đã bỏ buổi luyện."); go("t/home"); } catch (e) { showError(e, null); }
    });
    $("#finish", main).addEventListener("click", async () => {
      if (finishing) return;
      const hasTutorMsg = log.querySelector(".msg.me:not(.failed)");
      if (!hasTutorMsg) return toast("Hãy nhắn ít nhất một tin cho Nam trước khi kết thúc.");
      finishing = true;
      const btn = $("#finish", main); btn.disabled = true; btn.textContent = "Đang chấm điểm…";
      try { await api.finishSession(id); go("t/report/" + id); } catch (e) {
        finishing = false; btn.disabled = false; btn.textContent = "Kết thúc buổi luyện";
        showError({ ...e, message: "Chưa chấm được: " + e.message }, () => $("#finish", main).click());
      }
    });
  }
  $("#collapse", main).addEventListener("click", () => {
    collapsed = !collapsed;
    $("#pcols", main).classList.toggle("collapsed", collapsed);
    $("#geo", main).classList.toggle("hidden", collapsed);
    $("#collapse", main).textContent = collapsed ? "Mở rộng" : "Thu gọn";
    if (collapsed) $("#geo", main).insertAdjacentHTML("afterend", `<p class="small muted" id="geo-note">Vùng minh họa đang được thu gọn để mở rộng khung hội thoại.</p>`);
    else { $("#geo-note", main)?.remove(); renderGeoGebra($("#geo", main), s.geogebra_commands, 380, "Bài này chưa có hình minh họa."); }
  });
  renderGeoGebra($("#geo", main), s.geogebra_commands, 380, "Bài này chưa có hình minh họa.");
}

// ======================= BÁO CÁO =======================
export async function reports(main, { user }) {
  const sessions = (await api.tutorSessions(user.id)).filter((x) => x.status === "finished");
  main.innerHTML = `
    <section class="card"><h1 class="headline-s">Báo cáo</h1><p class="muted" style="margin:6px 0 0">Nhận xét theo 5 tiêu chí và gợi ý của Coach Agent sau mỗi buổi luyện.</p></section>
    <section class="card stack" style="padding-bottom:110px">
      ${sessions.length ? `<div class="row"><h2 class="title-l grow">Các buổi đã chấm</h2><span class="label-m muted">${sessions.length} buổi</span></div>
          <div class="hist">${sessions.map(histItem).join("")}</div>`
        : `<div class="empty" style="padding:40px"><div class="pics"><img src="${IMG}shark-hi.svg" alt="" width="110" /></div><b>Chưa có báo cáo nào</b>
            <span>Hoàn thành một buổi luyện để nhận báo cáo đánh giá.</span><a class="btn" href="#/t/home" style="margin-top:12px">Bắt đầu buổi luyện</a></div>`}
      ${wave()}
    </section>`;
}

export async function report(main, { params, user, go }) {
  const id = params.id;
  const [r, s] = await Promise.all([api.report(id), api.session(id).catch(() => null)]);
  const isMgr = user.role === "manager";
  const crit = r.criteria?.length ? r.criteria : Object.entries(r.scores).map(([k, v]) => ({ key: k, name: k, score: v, evidence: r.evidence.filter((e) => e.criterion === k) }));
  const minScore = Math.min(...crit.map((c) => c.score ?? 4));
  main.innerHTML = `
    <section class="card pad-sm row" style="gap:24px">
      <div class="grow"><h1 class="headline-s">Báo cáo buổi luyện</h1>
        <div class="row" style="gap:8px;margin-top:10px">
          <span class="chip">Chuyên đề: ${esc(topicName(r.chuyen_de))}</span><span class="chip">Học sinh ảo: Nam – ${esc(r.persona_name || "")}</span>
          <span class="chip">${fmtDateTime(r.created_at)}</span><span class="chip">Thời lượng: ${fmtMinutes(r.duration_min)}</span></div></div>
      <div class="score-box"><img src="${IMG}shark-cheer.svg" alt="" /><div><div class="label-l">ĐIỂM TỔNG</div><div class="label-m">Thang điểm 4</div></div>
        <div><span class="num">${fmtScore(r.total)}</span> <span class="of">/4</span></div></div>
    </section>
    <div class="cols">
      <section class="card stack" style="gap:10px;padding-bottom:90px">
        <div class="row"><h2 class="title-l grow">Đánh giá năng lực giảng dạy</h2><span class="label-m muted">5 tiêu chí · thang 4</span></div>
        ${crit.map((c, k) => {
          const ev = c.evidence || [];
          const low = c.score === minScore && minScore < 4;
          return `<div class="crit"><div class="crit-head"><span class="n">${k + 1}</span><span class="t">${esc(c.name)}</span>
              <span class="pill sm ${low ? "warn" : ""}">${c.score ?? "–"}/4</span></div>
            <div class="bar ${low ? "warn" : ""}"><i style="width:${((c.score || 0) / 4) * 100}%"></i></div>
            ${ev.length ? ev.map((e) => `<p><b>Nhận xét:</b> ${esc(e.comment)}</p><p class="ev"><b>Dẫn chứng:</b> “${esc(e.quote)}”</p>`).join("")
              : `<p class="ev">Chưa có dẫn chứng cho tiêu chí này.</p>`}</div>`;
        }).join("")}
        ${s?.messages?.length ? `<details class="transcript"><summary>Xem lại toàn bộ hội thoại (${s.messages.length} tin nhắn)</summary>
          <div class="stack" style="margin-top:12px">${s.messages.map((m) => `<div class="msg ${m.role === "tutor" ? "me" : ""}"><div class="body"><span class="who">${m.role === "tutor" ? "Gia sư" : "Nam"}</span><div class="bubble">${esc(m.content)}</div></div></div>`).join("")}</div></details>` : ""}
        ${wave("sm")}
      </section>
      <section class="card stack" style="gap:16px;padding-bottom:150px">
        <div class="row"><span class="avatar" style="width:48px;height:48px"><img src="${IMG}shark-tutor.svg" alt="" /></span><h2 class="title-l grow">Gợi ý từ Coach Agent</h2></div>
        <p class="body-l" style="margin:0">${esc(r.feedback)}</p>
        <div class="next-box">
          <span class="label-l" style="color:var(--on-primary-container)">BUỔI LUYỆN TIẾP THEO</span>
          <div class="r"><span class="k">Chuyên đề</span><span class="v">${esc(r.next_topic || topicName(r.next_chuyen_de))}</span></div>
          <div class="r"><span class="k">Tính cách học sinh</span><span class="v">${esc(r.next_persona_name || "Ngẫu nhiên")}</span></div>
          <div class="r"><span class="k">Lý do</span><span class="v">${esc(r.next_reason || r.next_recommendation || "–")}</span></div>
        </div>
        <div class="center-col">
          ${isMgr ? `<button class="btn outline" id="back">Quay lại</button>` : `
            <button class="btn lg" id="again">Luyện theo gợi ý</button><a class="btn outline lg" href="#/t/home">Về trang chủ</a>`}
        </div>
        <div id="again-err"></div>
        ${deco("deco-cloud.svg", "left:12%;bottom:40px")}${deco("deco-coral.svg", "left:42%;bottom:20px")}${deco("deco-crab.svg", "right:10%;bottom:40px")}
        ${wave()}
      </section>
    </div>`;
  if (isMgr) $("#back", main).addEventListener("click", () => history.back());
  else $("#again", main).addEventListener("click", async () => {
    const btn = $("#again", main); btn.disabled = true; btn.textContent = "Đang chuẩn bị…";
    try {
      const n = await api.startSession(r.next_chuyen_de || r.chuyen_de, r.next_persona, r.next_misconception_id);
      go("t/practice/" + n.session_id);
    } catch (e) { btn.disabled = false; btn.textContent = "Luyện theo gợi ý"; $("#again-err", main).innerHTML = errorBox(e, ""); }
  });
}
