import { useEffect, useRef, useState } from "react";
import { getExam, submitAttempt } from "../api.js";

const mmss = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

export default function Exam({ student, examId, onDone, onExit }) {
  const [exam, setExam] = useState(null);
  const [answers, setAnswers] = useState({});
  const [left, setLeft] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const startedAt = useRef(null);
  const answersRef = useRef({});
  answersRef.current = answers;

  useEffect(() => {
    getExam(examId).then((e) => { setExam(e); setLeft(e.time_limit_min * 60); startedAt.current = Date.now(); });
  }, [examId]);

  async function submit() {
    if (submitting) return;
    setSubmitting(true);
    const filled = Object.fromEntries(exam.questions.map((q) => [q.id, answersRef.current[q.id] ?? null]));
    const spent = Math.round((Date.now() - startedAt.current) / 1000);
    const result = await submitAttempt(student.id, examId, filled, spent);
    onDone(result);
  }

  // Đồng hồ đếm ngược, hết giờ tự nộp
  useEffect(() => {
    if (left === null || submitting) return;
    if (left <= 0) { submit(); return; }
    const t = setTimeout(() => setLeft((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [left, submitting]);

  if (!exam) return <p className="muted center">Đang tải đề…</p>;
  const done = Object.values(answers).filter(Boolean).length;
  const total = exam.questions.length;

  function confirmSubmit() {
    if (done < total && !window.confirm(`Bạn còn ${total - done} câu chưa làm. Vẫn nộp bài?`)) return;
    submit();
  }

  return (
    <section className="exam">
      <div className="exam-bar">
        <button className="link" onClick={() => { if (window.confirm("Thoát sẽ không lưu bài làm. Thoát?")) onExit(); }}>Thoát</button>
        <span className="exam-name">{exam.title}</span>
        <span className={left <= 60 ? "timer low" : "timer"} aria-live="off">{mmss(Math.max(0, left))}</span>
      </div>

      <ol className="questions">
        {exam.questions.map((q, i) => (
          <li key={q.id} className="q">
            <p className="q-text"><span className="q-num">Câu {i + 1}.</span> {q.content}</p>
            <div className="opts" role="radiogroup" aria-label={`Câu ${i + 1}`}>
              {Object.entries(q.options).map(([k, v]) => (
                <label key={k} className={answers[q.id] === k ? "opt on" : "opt"}>
                  <input type="radio" name={q.id} value={k} checked={answers[q.id] === k}
                    onChange={() => setAnswers((a) => ({ ...a, [q.id]: k }))} />
                  <span className="opt-key">{k}</span><span>{v}</span>
                </label>
              ))}
            </div>
          </li>
        ))}
      </ol>

      <div className="exam-foot">
        <span className="muted">Đã làm {done}/{total} câu</span>
        <button className="btn primary" onClick={confirmSubmit} disabled={submitting}>{submitting ? "Đang chấm…" : "Nộp bài"}</button>
      </div>
    </section>
  );
}
