import EXAMS_MOCK from "./exams-mock.json"; // dữ liệu đề giả, sinh từ data/exams/*.json
// Mọi lời gọi backend đều đi qua file này.
// Mặc định gọi backend thật theo docs/api-contract.md.
// Muốn làm giao diện khi chưa bật backend: tạo file frontend/.env.local với dòng VITE_USE_MOCK=1
const USE_MOCK = import.meta.env?.VITE_USE_MOCK === "1";
const API_URL = import.meta.env?.VITE_API_URL || "http://localhost:8000";

// ---------------- TOKEN ĐĂNG NHẬP ----------------
// Lưu trong localStorage của trình duyệt (bọc try/catch vì có trình duyệt chặn).
const TOKEN_KEY = "tutorsim_token";
let token = null;
try { token = localStorage.getItem(TOKEN_KEY); } catch { /* chế độ ẩn danh */ }
let onUnauthorized = () => {};
export function setOnUnauthorized(fn) { onUnauthorized = fn; }
export function hasToken() { return !!token; }
function saveToken(t) {
  token = t;
  try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch { /* bỏ qua */ }
}
export function logout() { saveToken(null); }

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_URL}${path}`, { headers, ...options });
  if (res.status === 401 && !path.startsWith("/api/auth/")) {
    saveToken(null);
    onUnauthorized();
  }
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail; } catch { /* không có JSON */ }
    throw new Error(detail || `Lỗi API ${res.status}: ${path}`);
  }
  return res.json();
}

// ---------------- DỮ LIỆU GIẢ ----------------
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const PROBLEMS = {
  ham_so: {
    topic: "Hàm số – Cực trị",
    problem: "Tìm các điểm cực trị của hàm số y = x³ − 3",
    student_solution: "y' = 3x²\nCho y' = 0 ⇔ x = 0\nVậy hàm số đạt cực trị tại x = 0.",
    geogebra_commands: ["f(x) = x^3 - 3"],
    replies: [
      "Nhưng y'(0) = 0 mà thầy? Em tưởng thế là có cực trị rồi ạ…",
      "Hai bên x = 0 thì y' đều dương ạ… vậy là sao hả thầy?",
      "À, y' không đổi dấu nên x = 0 không phải cực trị. Hàm này không có cực trị ạ!",
    ],
  },
  oxyz: {
    topic: "Oxyz – Khoảng cách",
    problem: "Tính khoảng cách từ A(1; 2; 3) đến mặt phẳng (P): 2x − y + 2z + 1 = 0",
    student_solution: "d = |2.1 − 2 + 2.3 + 1|\n  = |7| = 7",
    geogebra_commands: ["A = (1, 2, 3)", "P: 2x - y + 2z + 1 = 0"],
    replies: [
      "Em thay đúng tọa độ A vào rồi mà thầy, sao lại sai ạ?",
      "Phải chia cho cái gì nữa ạ? Em nhớ công thức chỉ có trị tuyệt đối thôi…",
      "À em hiểu rồi, phải chia cho √(2² + 1² + 2²) = 3, nên d = 7/3 ạ!",
    ],
  },
};
const mock = {
  tutors: [{ id: 1, name: "Minh" }, { id: 2, name: "Lan" }, { id: 3, name: "Tuấn" }],
  sessions: {},
  history: [
    { tutor_id: 1, session_id: 101, topic: "Hàm số – Cực trị", total: 2.9, created_at: "2026-10-08T19:30:00" },
    { tutor_id: 1, session_id: 102, topic: "Oxyz – Khoảng cách", total: 3.3, created_at: "2026-10-10T20:05:00" },
  ],
  nextId: 1,
};

// ---------------- CÁC HÀM GỌI API ----------------
// ---------------- TÀI KHOẢN ----------------
const MOCK_USERS = {
  minh: { id: 1, username: "minh", name: "Minh", role: "tutor" },
  ha: { id: 1, username: "ha", name: "Hà", role: "student" },
  quanly: { id: 9, username: "quanly", name: "Quản lý trung tâm", role: "manager" },
};
let mockMe = null;

export async function login(username, password) {
  if (USE_MOCK) {
    await wait(200);
    const u = MOCK_USERS[username.trim().toLowerCase()];
    if (!u) throw new Error("Chế độ giả: dùng minh, ha hoặc quanly (mật khẩu bất kỳ)");
    mockMe = u; saveToken("mock"); return { token: "mock", user: u };
  }
  const r = await request("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
  saveToken(r.token);
  return r;
}

export async function register(username, password, name, role) {
  if (USE_MOCK) {
    mockMe = { id: 20, username, name, role }; saveToken("mock"); return { token: "mock", user: mockMe };
  }
  const r = await request("/api/auth/register", { method: "POST", body: JSON.stringify({ username, password, name, role }) });
  saveToken(r.token);
  return r;
}

export async function getMe() {
  if (USE_MOCK) {
    if (!mockMe) throw new Error("Chưa đăng nhập");
    return mockMe;
  }
  return request("/api/auth/me");
}

export async function getHealth() {
  if (USE_MOCK) return { allow_register: true };
  return request("/api/health");
}

export async function getTutors() {
  if (USE_MOCK) return mock.tutors;
  return request("/api/tutors");
}

export async function getTutorSessions(tutorId) {
  if (USE_MOCK) return mock.history.filter((s) => s.tutor_id === tutorId).slice().reverse();
  return request(`/api/tutors/${tutorId}/sessions`);
}

export async function startSession(tutorId, chuyenDe = "ham_so", misconceptionId = null, persona = null) {
  if (USE_MOCK) {
    await wait(400);
    const p = PROBLEMS[chuyenDe];
    const id = mock.nextId++;
    mock.sessions[id] = { tutor_id: tutorId, chuyenDe, turn: 0 };
    const { replies, ...rest } = p;
    return { session_id: id, student_name: "Nam", ...rest };
  }
  return request("/api/sessions", { method: "POST", body: JSON.stringify({ chuyen_de: chuyenDe,
    misconception_id: misconceptionId, persona }) });
}

export async function sendMessage(sessionId, content) {
  if (USE_MOCK) {
    await wait(900);
    const s = mock.sessions[sessionId];
    const replies = PROBLEMS[s.chuyenDe].replies;
    const i = Math.min(s.turn, replies.length - 1);
    s.turn += 1;
    return { student_reply: replies[i], math_warnings: [], status: i === replies.length - 1 ? "student_understood" : "in_progress" };
  }
  return request(`/api/sessions/${sessionId}/messages`, { method: "POST", body: JSON.stringify({ content }) });
}

export async function finishSession(sessionId) {
  if (USE_MOCK) {
    await wait(1200);
    const s = mock.sessions[sessionId];
    mock.history.push({ tutor_id: s.tutor_id, session_id: sessionId, topic: PROBLEMS[s.chuyenDe].topic, total: 3.6, created_at: new Date().toISOString() });
    return { report_id: sessionId };
  }
  return request(`/api/sessions/${sessionId}/finish`, { method: "POST", body: "{}" });
}

export async function getReport(reportId) {
  if (USE_MOCK) {
    return {
      report_id: reportId,
      scores: { chinh_xac: 4, chan_doan: 4, ro_rang: 3, goi_mo: 3, thai_do: 4 },
      total: 3.6,
      evidence: [
        { criterion: "chan_doan", quote: "Em thử xem y' có đổi dấu khi đi qua x = 0 không?", comment: "Nhắm đúng vào nguyên nhân gốc của lỗi." },
        { criterion: "goi_mo", quote: "Vậy muốn có cực trị thì y' cần thêm điều kiện gì?", comment: "Câu hỏi dẫn dắt để Nam tự rút ra kết luận." },
        { criterion: "ro_rang", quote: "Điều kiện y' = 0 là cần nhưng chưa đủ đâu em.", comment: "Đúng nhưng nên kèm một ví dụ để Nam dễ hình dung." },
      ],
      feedback: "Bạn tìm ra đúng chỗ sai và dẫn dắt bằng câu hỏi thay vì giải hộ. Lần sau, hãy để Nam tự phát biểu lại kết luận trước khi xác nhận, để chắc em đã hiểu thật.",
      next_recommendation: "Luyện với học sinh hay cãi ở chuyên đề Oxyz",
      next_chuyen_de: "oxyz",
    };
  }
  return request(`/api/reports/${reportId}`);
}

export async function getDashboard() {
  if (USE_MOCK) {
    return mock.tutors.map((t) => {
      const mine = mock.history.filter((h) => h.tutor_id === t.id);
      const avg = mine.length ? mine.reduce((a, b) => a + b.total, 0) / mine.length : null;
      const last = mine.length ? mine[mine.length - 1].created_at.slice(0, 10) : null;
      return { tutor_id: t.id, name: t.name, sessions_count: mine.length, avg_total: avg && Math.round(avg * 10) / 10, last_session: last };
    });
  }
  return request("/api/dashboard");
}

// =====================================================================
// ======================= PHÂN HỆ 2: LUYỆN ĐỀ ==========================
// =====================================================================

const mock2 = {
  students: [{ id: 1, name: "Hà" }, { id: 2, name: "Khoa" }],
  attempts: [
    // 2 bài cũ của Hà để demo phần dự đoán
    { attempt_id: 901, student_id: 1, exam_title: "Đề luyện 01 – Hàm số", score10: 6, created_at: "2026-10-05T19:00:00",
      results: [{ misconception_id: "HS-07" }, { misconception_id: "HS-12" }, { misconception_id: "HS-07" }] },
    { attempt_id: 902, student_id: 1, exam_title: "Đề luyện 02 – Oxyz", score10: 7, created_at: "2026-10-08T20:30:00",
      results: [{ misconception_id: "OX-01" }, { misconception_id: "OX-04" }] },
  ],
};
const ALL_NAMES = Object.assign({}, ...EXAMS_MOCK.map((e) => e.misconception_names));

function predictMock(scores) {
  if (scores.length < 2) return null;
  const last = scores.slice(-3);
  const w = last.map((_, i) => i + 1);
  const mid = last.reduce((a, s, i) => a + s * w[i], 0) / w.reduce((a, b) => a + b, 0);
  const mean = last.reduce((a, b) => a + b, 0) / last.length;
  const sd = Math.sqrt(last.reduce((a, s) => a + (s - mean) ** 2, 0) / last.length);
  const spread = Math.max(0.5, sd);
  const r = (v) => Math.round(v * 10) / 10;
  return { low: r(Math.max(0, mid - spread)), mid: r(mid), high: r(Math.min(10, mid + spread)) };
}
function topMis(attempts, limit = 5) {
  const c = {};
  attempts.forEach((a) => a.results.forEach((r) => { if (r.misconception_id) c[r.misconception_id] = (c[r.misconception_id] || 0) + 1; }));
  return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, limit).map(([id, count]) => ({ id, name: ALL_NAMES[id] || id, count }));
}

export async function getStudents() {
  if (USE_MOCK) return mock2.students;
  return request("/api/students");
}

export async function getExams() {
  if (USE_MOCK) return EXAMS_MOCK.map((e) => ({ id: e.id, title: e.title, chuyen_de: e.chuyen_de, num_questions: e.questions.length, time_limit_min: e.time_limit_min }));
  return request("/api/exams");
}

export async function getExam(examId) {
  if (USE_MOCK) {
    const e = EXAMS_MOCK.find((x) => x.id === examId);
    return { id: e.id, title: e.title, time_limit_min: e.time_limit_min, questions: e.questions.map(({ id, content, options }) => ({ id, content, options })) };
  }
  return request(`/api/exams/${examId}`);
}

export async function submitAttempt(studentId, examId, answers, timeSpentSec) {
  if (USE_MOCK) {
    await wait(500);
    const e = EXAMS_MOCK.find((x) => x.id === examId);
    let correct = 0;
    const results = e.questions.map((q) => {
      const chosen = answers[q.id] ?? null;
      const ok = chosen === q.answer;
      if (ok) correct++;
      const mis = !ok && chosen ? q.misconceptions[chosen] || null : null;
      return { question_id: q.id, chosen, correct_answer: q.answer, is_correct: ok, misconception_id: mis,
        misconception_name: mis ? e.misconception_names[mis] : null, explanation: q.explanation };
    });
    const attempt = { attempt_id: mock2.attempts.length + 1, student_id: studentId, exam_title: e.title, correct, total: e.questions.length,
      score10: Math.round((correct / e.questions.length) * 1000) / 100, time_spent_sec: timeSpentSec, created_at: new Date().toISOString(), results };
    mock2.attempts.push(attempt);
    return attempt;
  }
  return request("/api/attempts", { method: "POST", body: JSON.stringify({ exam_id: examId, answers, time_spent_sec: timeSpentSec }) });
}

export async function getStudentSummary(studentId) {
  if (USE_MOCK) {
    const mine = mock2.attempts.filter((a) => a.student_id === studentId);
    return {
      attempts: mine.slice().reverse().map(({ attempt_id, exam_title, score10, created_at }) => ({ attempt_id, exam_title, score10, created_at })),
      top_misconceptions: topMis(mine),
      prediction: predictMock(mine.map((a) => a.score10)),
      note: "Ước lượng điểm môn Toán (chỉ 2 chuyên đề Hàm số, Oxyz) từ các bài luyện gần nhất, không phải cam kết.",
    };
  }
  return request(`/api/students/${studentId}/summary`);
}

export async function getMisconceptionInsights() {
  if (USE_MOCK) return topMis(mock2.attempts, 10);
  return request("/api/insights/misconceptions");
}
