// Tiện ích giao diện dùng chung: escape HTML, hộp thoại, thông báo, định dạng, GeoGebra.
export const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
export const IMG = "assets/img/";

export function fmtDateTime(iso) {
  if (!iso) return "–";
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} · ${p(d.getHours())}:${p(d.getMinutes())}`;
}
export function fmtMinutes(min) {
  if (min == null) return "–";
  const h = Math.floor(min / 60), m = min % 60;
  return h ? `${h} giờ ${m} phút` : `${m} phút`;
}
export const fmtScore = (v, digits = 1) => (v == null ? "–" : Number(v).toFixed(digits));
export const fmtVi = (v, digits = 1) => (v == null ? "–" : Number(v).toFixed(digits).replace(".", ","));

export function toast(msg, ms = 3800) {
  const root = document.getElementById("toast");
  root.innerHTML = `<div class="t">${esc(msg)}</div>`;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { root.innerHTML = ""; }, ms);
}

/** Hộp thoại xác nhận. Trả về Promise<boolean>. */
export function confirmDialog({ title, message, ok = "Đồng ý", cancel = "Hủy", danger = false, pic = "shark-study.svg", hideCancel = false }) {
  return new Promise((resolve) => {
    const root = document.getElementById("modal-root");
    root.innerHTML = `
      <div class="overlay" role="presentation">
        <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dlg-t">
          ${pic ? `<img class="pic" src="${IMG}${pic}" alt="" />` : ""}
          <h2 id="dlg-t">${esc(title)}</h2>
          <p>${esc(message)}</p>
          <div class="acts">
            ${hideCancel ? "" : `<button class="btn outline" data-v="0">${esc(cancel)}</button>`}
            <button class="btn ${danger ? "danger" : "strong"}" data-v="1">${esc(ok)}</button>
          </div>
        </div>
      </div>`;
    const done = (v) => { root.innerHTML = ""; document.removeEventListener("keydown", onKey); resolve(v); };
    const onKey = (e) => { if (e.key === "Escape" && !hideCancel) done(false); };
    document.addEventListener("keydown", onKey);
    $$("[data-v]", root).forEach((b) => b.addEventListener("click", () => done(b.dataset.v === "1")));
    $(".overlay", root).addEventListener("click", (e) => { if (e.target.classList.contains("overlay") && !hideCancel) done(false); });
    $(`[data-v="1"]`, root).focus();
  });
}

/** Hộp thoại có biểu mẫu. fields: [{name,label,type,value,placeholder}]. onSubmit(values) trả lỗi (string) hoặc null. */
export function formDialog({ title, fields, ok = "Lưu", onSubmit }) {
  const root = document.getElementById("modal-root");
  root.innerHTML = `
    <div class="overlay">
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dlg-t">
        <button class="close" aria-label="Đóng">×</button>
        <h2 id="dlg-t">${esc(title)}</h2>
        <form novalidate>
          ${fields.map((f) => `
            <label class="tf"><span>${esc(f.label)}</span>
              <input name="${f.name}" type="${f.type || "text"}" value="${esc(f.value || "")}" placeholder="${esc(f.placeholder || "")}"
                ${f.autocomplete ? `autocomplete="${f.autocomplete}"` : ""} required /></label>`).join("")}
          <p class="form-error hidden" role="alert"></p>
          <div class="acts"><button type="button" class="btn outline" data-cancel>Hủy</button><button class="btn strong" type="submit">${esc(ok)}</button></div>
        </form>
      </div>
    </div>`;
  const close = () => { root.innerHTML = ""; };
  $(".close", root).addEventListener("click", close);
  $("[data-cancel]", root).addEventListener("click", close);
  const form = $("form", root);
  $("input", form)?.focus();
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(form).entries());
    const btn = $("button[type=submit]", form);
    btn.disabled = true;
    const err = await onSubmit(values);
    btn.disabled = false;
    const box = $(".form-error", form);
    if (err) { box.textContent = err; box.classList.remove("hidden"); } else close();
  });
}

export const closeModal = () => { document.getElementById("modal-root").innerHTML = ""; };

export function errorBox(err, retryLabel = "Thử lại") {
  return `<div class="notice error" role="alert"><span class="i">!</span><div class="grow">${esc(err?.message || err)}</div>
    ${retryLabel ? `<button class="btn outline danger" data-retry>${esc(retryLabel)}</button>` : ""}</div>`;
}

export const placeholderSvg = `<svg viewBox="0 0 40 40" fill="currentColor" aria-hidden="true"><path d="M20 4l8 12H12z"/><circle cx="12" cy="28" r="7"/><rect x="22" y="21" width="14" height="14" rx="3"/></svg>`;

export const icons = {
  bars: `<svg viewBox="0 0 26 26" fill="currentColor"><rect x="3" y="15" width="5" height="9" rx="2"/><rect x="11" y="8" width="5" height="16" rx="2"/><rect x="19" y="1" width="5" height="23" rx="2"/></svg>`,
  doc: `<svg viewBox="0 0 26 30" fill="none"><rect x="2" y="1" width="22" height="28" rx="5" fill="currentColor" opacity=".18"/><rect x="7" y="9" width="12" height="2.6" rx="1.3" fill="currentColor"/><rect x="7" y="15" width="10" height="2.6" rx="1.3" fill="currentColor"/><rect x="7" y="21" width="8" height="2.6" rx="1.3" fill="currentColor"/></svg>`,
  alertDoc: `<svg viewBox="0 0 26 26" fill="none"><rect x="3" y="1" width="18" height="24" rx="5" fill="#e0d9fa"/><rect x="7" y="7" width="10" height="2.4" rx="1.2" fill="#e37c9c"/><rect x="7" y="12" width="8" height="2.4" rx="1.2" fill="#e37c9c"/><rect x="7" y="17" width="6" height="2.4" rx="1.2" fill="#e37c9c"/><circle cx="20" cy="20" r="5.5" fill="#e0516f"/><rect x="19.2" y="16.8" width="1.6" height="4" rx=".8" fill="#fff"/><circle cx="20" cy="22.8" r=".9" fill="#fff"/></svg>`,
  clock: `<svg viewBox="0 0 26 26" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="13" cy="13" r="9.5"/><path d="M13 8v5.5l3.5 2" stroke-linecap="round"/></svg>`,
};

// ---------------- GeoGebra (nhúng như frontend cũ) ----------------
const GGB = "https://www.geogebra.org/apps/deployggb.js";
let ggbLoading = null;
function loadGgb() {
  if (window.GGBApplet) return Promise.resolve();
  if (!ggbLoading) {
    ggbLoading = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = GGB; s.onload = resolve;
      s.onerror = () => { ggbLoading = null; reject(new Error("Không tải được GeoGebra")); };
      document.head.appendChild(s);
    });
  }
  return ggbLoading;
}
let ggbCount = 0;
/** Vẽ các lệnh GeoGebra vào phần tử box. */
export async function renderGeoGebra(box, commands, height = 320, emptyMsg = "Không có đồ thị cho câu hỏi hiện tại.") {
  if (!commands || !commands.length) {
    box.innerHTML = `<div class="geo-empty">${esc(emptyMsg)}</div>`;
    return;
  }
  const id = `ggb-${++ggbCount}`;
  box.innerHTML = `<div id="${id}"></div>`;
  const is3d = commands.some((c) => /z|\(\s*-?[\d/.]+\s*,\s*-?[\d/.]+\s*,\s*-?[\d/.]+\s*\)/.test(c));
  try {
    await loadGgb();
    if (!document.getElementById(id)) return;
    const width = Math.max(260, box.clientWidth - 2);
    const applet = new window.GGBApplet({
      appName: is3d ? "3d" : "graphing", width, height, showToolBar: false, showAlgebraInput: false, showMenuBar: false,
      showResetIcon: true, enableShiftDragZoom: true, language: "vi",
      appletOnLoad: (a) => commands.forEach((c) => { try { a.evalCommand(c); } catch { /* bỏ qua lệnh lỗi */ } }),
    }, true);
    applet.inject(id);
  } catch (e) {
    box.innerHTML = `<div class="geo-empty">${esc(e.message)}.<br/>Lệnh vẽ: <code>${esc(commands.join("; "))}</code></div>`;
  }
}

export const wave = (cls = "") => `<div class="waves ${cls}" aria-hidden="true"></div>`;
export const deco = (file, style, w = 84) => `<img class="deco mobile_hide_unneccessary" src="${IMG}${file}" alt="" style="width:${w}px;${style}" />`;
