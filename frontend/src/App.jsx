import { useEffect, useState } from "react";
import { getMe, hasToken, logout, setOnUnauthorized } from "./api.js";
import Login from "./pages/Login.jsx";
import Home from "./pages/Home.jsx";
import Practice from "./pages/Practice.jsx";
import Report from "./pages/Report.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import StudentHome from "./pages/StudentHome.jsx";
import Exam from "./pages/Exam.jsx";
import ExamResult from "./pages/ExamResult.jsx";

const HOME = { tutor: "home", student: "studentHome", manager: "dashboard" };
const ROLE_LABEL = { tutor: "Gia sư", student: "Học sinh", manager: "Quản lý" };

// Điều hướng đơn giản bằng state (MVP chưa cần react-router). Màn hình theo vai của tài khoản.
export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(hasToken());
  const [screen, setScreen] = useState({ name: "login" });
  const go = (name, params = {}) => setScreen({ name, ...params });

  function enter(u) { setUser(u); go(HOME[u.role] || "login"); }
  function signOut() { logout(); setUser(null); go("login"); }

  useEffect(() => {
    setOnUnauthorized(() => { setUser(null); go("login"); });
    if (hasToken()) getMe().then(enter).catch(() => logout()).finally(() => setChecking(false));
  }, []);

  if (checking) return <p className="muted center">Đang tải…</p>;
  const tutor = user?.role === "tutor" ? user : null;
  const student = user?.role === "student" ? user : null;

  return (
    <div className="app">
      <header className="topbar">
        <button className="brand" onClick={() => go(user ? HOME[user.role] : "login")}>
          <span className="brand-mark" aria-hidden="true">✓</span> TutorSim
        </button>
        {user && (
          <div className="who">
            <span>{ROLE_LABEL[user.role]}: <strong>{user.name}</strong></span>
            <button className="link" onClick={signOut}>Đăng xuất</button>
          </div>
        )}
      </header>
      <main className="main">
        {(!user || screen.name === "login") && <Login onLoggedIn={enter} />}

        {/* ---------- Phân hệ 1: gia sư ---------- */}
        {tutor && screen.name === "home" && <Home tutor={tutor} onStart={(cd) => go("practice", { chuyenDe: cd, nonce: Date.now() })} />}
        {tutor && screen.name === "practice" && (
          <Practice key={screen.nonce} tutor={tutor} chuyenDe={screen.chuyenDe} mid={screen.mid} persona={screen.persona}
            onFinish={(reportId) => go("report", { reportId })} onExit={() => go("home")} />
        )}
        {tutor && screen.name === "report" && (
          <Report reportId={screen.reportId} onAgain={(cd, mid, persona) => go("practice", { chuyenDe: cd, mid, persona, nonce: Date.now() })} onHome={() => go("home")} />
        )}

        {/* ---------- Phân hệ 2: học sinh ---------- */}
        {student && screen.name === "studentHome" && <StudentHome student={student} onStartExam={(id) => go("exam", { examId: id })} />}
        {student && screen.name === "exam" && (
          <Exam student={student} examId={screen.examId} onDone={(result) => go("examResult", { result })} onExit={() => go("studentHome")} />
        )}
        {student && screen.name === "examResult" && <ExamResult result={screen.result} onHome={() => go("studentHome")} />}

        {/* ---------- Quản lý trung tâm ---------- */}
        {user?.role === "manager" && screen.name === "dashboard" && <Dashboard />}
      </main>
    </div>
  );
}
