import { useState } from "react";
import ChooseTutor from "./pages/ChooseTutor.jsx";
import Home from "./pages/Home.jsx";
import Practice from "./pages/Practice.jsx";
import Report from "./pages/Report.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import StudentHome from "./pages/StudentHome.jsx";
import Exam from "./pages/Exam.jsx";
import ExamResult from "./pages/ExamResult.jsx";

// Điều hướng đơn giản bằng state (MVP chưa cần react-router)
export default function App() {
  const [screen, setScreen] = useState({ name: "choose" });
  const [tutor, setTutor] = useState(null);       // Phân hệ 1
  const [student, setStudent] = useState(null);   // Phân hệ 2
  const go = (name, params = {}) => setScreen({ name, ...params });
  const logout = () => { setTutor(null); setStudent(null); go("choose"); };
  const me = tutor ? { label: "Gia sư", name: tutor.name } : student ? { label: "Học sinh", name: student.name } : null;

  return (
    <div className="app">
      <header className="topbar">
        <button className="brand" onClick={() => go(tutor ? "home" : student ? "studentHome" : "choose")}>
          <span className="brand-mark" aria-hidden="true">✓</span> TutorSim
        </button>
        {me && screen.name !== "dashboard" && (
          <div className="who">
            <span>{me.label}: <strong>{me.name}</strong></span>
            <button className="link" onClick={logout}>Đổi người</button>
          </div>
        )}
      </header>
      <main className="main">
        {screen.name === "choose" && (
          <ChooseTutor
            onPick={(t) => { setTutor(t); setStudent(null); go("home"); }}
            onPickStudent={(s) => { setStudent(s); setTutor(null); go("studentHome"); }}
            onManager={() => go("dashboard")} />
        )}

        {/* ---------- Phân hệ 1: gia sư ---------- */}
        {screen.name === "home" && <Home tutor={tutor} onStart={(cd) => go("practice", { chuyenDe: cd, nonce: Date.now() })} />}
        {screen.name === "practice" && (
          <Practice key={screen.nonce} tutor={tutor} chuyenDe={screen.chuyenDe} mid={screen.mid} persona={screen.persona}
            onFinish={(reportId) => go("report", { reportId })} onExit={() => go("home")} />
        )}
        {screen.name === "report" && (
          <Report reportId={screen.reportId} onAgain={(cd, mid, persona) => go("practice", { chuyenDe: cd, mid, persona, nonce: Date.now() })} onHome={() => go("home")} />
        )}

        {/* ---------- Phân hệ 2: học sinh ---------- */}
        {screen.name === "studentHome" && <StudentHome student={student} onStartExam={(id) => go("exam", { examId: id })} />}
        {screen.name === "exam" && (
          <Exam student={student} examId={screen.examId} onDone={(result) => go("examResult", { result })} onExit={() => go("studentHome")} />
        )}
        {screen.name === "examResult" && <ExamResult result={screen.result} onHome={() => go("studentHome")} />}

        {/* ---------- Quản lý trung tâm ---------- */}
        {screen.name === "dashboard" && <Dashboard onBack={() => go(tutor ? "home" : student ? "studentHome" : "choose")} />}
      </main>
    </div>
  );
}
