import { useEffect, useRef, useState } from "react";
import { startSession, sendMessage, finishSession } from "../api.js";
import GeoGebra from "../components/GeoGebra.jsx";

export default function Practice({ tutor, chuyenDe, mid = null, persona = null, onFinish, onExit }) {
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [waiting, setWaiting] = useState(false);
  const [understood, setUnderstood] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [error, setError] = useState("");
  const [figOpen, setFigOpen] = useState(false);
  const chatEnd = useRef(null);

  useEffect(() => {
    startSession(tutor.id, chuyenDe, mid, persona).then(setSession).catch((e) => setError(`Không tạo được buổi luyện: ${e.message}`));
  }, [tutor.id, chuyenDe, mid, persona]);

  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [messages, waiting]);

  async function send() {
    const text = draft.trim();
    if (!text || waiting) return;
    setDraft("");
    setMessages((m) => [...m, { role: "tutor", text }]);
    setWaiting(true);
    try {
      const res = await sendMessage(session.session_id, text);
      setMessages((m) => [...m, { role: "student", text: res.student_reply, warnings: res.math_warnings }]);
      if (res.status === "student_understood") setUnderstood(true);
      setError("");
    } catch (e) {
      setMessages((m) => m.slice(0, -1));
      setDraft(text);
      setError(`Tin nhắn chưa gửi được: ${e.message}`);
    } finally {
      setWaiting(false);
    }
  }

  async function finish() {
    setFinishing(true);
    try {
      const { report_id } = await finishSession(session.session_id);
      onFinish(report_id);
    } catch (e) {
      setFinishing(false);
      setError(`Chưa chấm được: ${e.message}`);
    }
  }

  if (error && !session) return <p className="error">{error}</p>;
  if (!session) return <p className="muted center">Nam đang chuẩn bị bài…</p>;

  return (
    <section className="practice">
      <div className="worksheet">
        <p className="topic">{session.topic}</p>
        <h1 className="problem">{session.problem}</h1>
        <div className="paper" aria-label={`Bài làm của ${session.student_name}`}>
          <p className="paper-name">Bài làm của {session.student_name}</p>
          <pre className="hand">{session.student_solution}</pre>
        </div>
        {session.geogebra_commands.length > 0 && (
          <details className="figure" onToggle={(e) => setFigOpen(e.currentTarget.open)}>
            <summary>Hình minh họa (GeoGebra)</summary>
            <div className="figure-box">{figOpen && <GeoGebra commands={session.geogebra_commands} />}</div>
          </details>
        )}
      </div>

      <div className="chat">
        <div className="chat-log" aria-live="polite">
          {messages.length === 0 && (
            <p className="hint">Đọc bài làm của {session.student_name}, rồi bắt đầu chữa bài. Thử đặt câu hỏi để em tự nhận ra chỗ sai thay vì nói ngay đáp án.</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <span className="msg-who">{m.role === "tutor" ? "Bạn" : session.student_name}</span>
              <p>{m.text}</p>
              {m.warnings?.map((w, j) => <p key={j} className="warn">Kiểm tra lại: {w}</p>)}
            </div>
          ))}
          {waiting && <div className="msg student typing"><span className="msg-who">{session.student_name}</span><p>đang viết…</p></div>}
          <div ref={chatEnd} />
        </div>

        {understood && (
          <div className="understood" role="status">
            {session.student_name} có vẻ đã hiểu ra. Bạn có thể kết thúc buổi để xem nhận xét.
          </div>
        )}
        {error && <p className="error">{error}</p>}

        <div className="composer">
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={2}
            placeholder={`Nhắn cho ${session.student_name}…`} aria-label="Tin nhắn của bạn"
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} />
          <button className="btn primary" onClick={send} disabled={!draft.trim() || waiting}>Gửi</button>
        </div>
        <div className="chat-actions">
          <button className="link" onClick={onExit}>Bỏ buổi này</button>
          <button className={understood ? "btn primary" : "btn"} onClick={finish} disabled={finishing || messages.length === 0}>
            {finishing ? "Đang chấm…" : "Kết thúc và xem nhận xét"}
          </button>
        </div>
      </div>
    </section>
  );
}
