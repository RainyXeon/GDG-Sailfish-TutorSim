const TOKEN_KEY = "tutorsim_token";
let token = null;
try { token = localStorage.getItem(TOKEN_KEY); } catch { /* trình duyệt chặn bộ nhớ */ }
let onUnauthorized = () => {};
export const setOnUnauthorized = (fn) => { onUnauthorized = fn; };
export const hasToken = () => !!token;
function saveToken(t) {
  token = t;
  try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch { /* bỏ qua */ }
}
export const logout = () => saveToken(null);

export class ApiError extends Error {
  constructor(status, message, retryAfter) { super(message); this.status = status; this.retryAfter = retryAfter; }
}

function detailText(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
  return JSON.stringify(detail);
}

async function request(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError(0, "Không kết nối được máy chủ. Kiểm tra mạng hoặc thử lại sau ít phút.");
  }
  if (res.status === 401 && !path.startsWith("/api/auth/login") && !path.startsWith("/api/auth/register")) {
    saveToken(null);
    onUnauthorized();
  }
  if (!res.ok) {
    let detail = "";
    try { detail = detailText((await res.json()).detail); } catch { /* không có JSON */ }
    const retry = Number(res.headers.get("Retry-After")) || null;
    const fallback = { 502: "Máy chủ đang bận (502). Thử lại sau ít phút.", 503: "Dịch vụ tạm thời gián đoạn (503).",
      504: "Máy chủ phản hồi quá lâu (504). Thử lại sau ít phút." }[res.status];
    throw new ApiError(res.status, detail || fallback || `Lỗi ${res.status}`, retry);
  }
  return res.status === 204 ? null : res.json();
}

const enc = encodeURIComponent;

export const api = {
  // ---------- tài khoản ----------
  async login(username, password) {
    const r = await request("/api/auth/login", { method: "POST", body: { username, password } });
    saveToken(r.token); return r.user;
  },
  async register(username, password, name, role) {
    const r = await request("/api/auth/register", { method: "POST", body: { username, password, name, role } });
    saveToken(r.token); return r.user;
  },
  me: () => request("/api/auth/me"),
  health: () => request("/api/health"),
  updateMe: (name) => request("/api/auth/me", { method: "PATCH", body: { name } }),
  changePassword: (old_password, new_password) => request("/api/auth/change-password", { method: "POST", body: { old_password, new_password } }),
  forgotPassword: (username) => request("/api/auth/forgot-password", { method: "POST", body: { username } }),
  resetRequests: () => request("/api/auth/reset-requests"),
  resetPassword: (userId, new_password) => request(`/api/users/${userId}/reset-password`, { method: "POST", body: { new_password } }),

  // ---------- gia sư ----------
  personas: () => request("/api/personas"),
  rubric: () => request("/api/rubric"),
  tutorStats: (id) => request(`/api/tutors/${id}/stats`),
  tutorSessions: (id, includeUnfinished = false) => request(`/api/tutors/${id}/sessions${includeUnfinished ? "?include_unfinished=true" : ""}`),
  startSession: (chuyen_de, persona = null, misconception_id = null) =>
    request("/api/sessions", { method: "POST", body: { chuyen_de, persona, misconception_id } }),
  session: (id) => request(`/api/sessions/${id}`),
  sendMessage: (id, content) => request(`/api/sessions/${id}/messages`, { method: "POST", body: { content } }),
  finishSession: (id) => request(`/api/sessions/${id}/finish`, { method: "POST", body: {} }),
  abandonSession: (id) => request(`/api/sessions/${id}/abandon`, { method: "POST", body: {} }),
  report: (id) => request(`/api/reports/${id}`),

  // ---------- học sinh ----------
  exams: () => request("/api/exams"),
  exam: (id) => request(`/api/exams/${enc(id)}`),
  startExam: (id) => request(`/api/exams/${enc(id)}/start`, { method: "POST", body: {} }),
  submitAttempt: (exam_id, answers, time_spent_sec, attempt_token) =>
    request("/api/attempts", { method: "POST", body: { exam_id, answers, time_spent_sec, attempt_token } }),
  attempt: (id) => request(`/api/attempts/${id}`),
  studentSummary: (id) => request(`/api/students/${id}/summary`),

  // ---------- quản lý ----------
  dashboard: (q = "") => request(`/api/dashboard${q ? "?q=" + enc(q) : ""}`),
  overview: () => request("/api/dashboard/overview"),
  topics: (chuyen_de = "") => request(`/api/dashboard/topics${chuyen_de ? "?chuyen_de=" + enc(chuyen_de) : ""}`),
  insights: () => request("/api/insights/misconceptions"),
};
