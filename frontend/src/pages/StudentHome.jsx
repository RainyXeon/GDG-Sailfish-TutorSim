import { useEffect, useState } from "react";
import { getExams, getStudentSummary } from "../api.js";
import { formatDate } from "../constants.js";

export default function StudentHome({ student, onStartExam }) {
  const [exams, setExams] = useState(null);
  const [sum, setSum] = useState(null);

  useEffect(() => {
    getExams().then(setExams);
    getStudentSummary(student.id).then(setSum);
  }, [student.id]);

  return (
    <section className="narrow">
      <h1 className="title">Chào {student.name}</h1>

      <div className="predict">
        <p className="predict-label">Điểm Toán dự kiến</p>
        {sum?.prediction ? (
          <p className="predict-range">{sum.prediction.low.toFixed(1)} – {sum.prediction.high.toFixed(1)}</p>
        ) : (
          <p className="muted">Làm ít nhất 2 đề để xem điểm dự kiến.</p>
        )}
        {sum && <p className="predict-note">{sum.note}</p>}
      </div>

      <h2 className="h2">Đề luyện</h2>
      {!exams && <p className="muted">Đang tải…</p>}
      <ul className="exam-list">
        {exams?.map((e) => (
          <li key={e.id}>
            <div>
              <p className="exam-title">{e.title}</p>
              <p className="muted small">{e.num_questions} câu, {e.time_limit_min} phút</p>
            </div>
            <button className="btn primary" onClick={() => onStartExam(e.id)}>Làm đề</button>
          </li>
        ))}
      </ul>

      {sum?.top_misconceptions.length > 0 && (
        <>
          <h2 className="h2">Lỗi bạn hay mắc</h2>
          <ul className="mis-list">
            {sum.top_misconceptions.map((m) => (
              <li key={m.id}><span>{m.name}</span><span className="mis-count">{m.count} lần</span></li>
            ))}
          </ul>
        </>
      )}

      <h2 className="h2">Bài đã làm</h2>
      {sum?.attempts.length === 0 && <p className="muted">Chưa có bài nào.</p>}
      <ul className="history">
        {sum?.attempts.map((a) => (
          <li key={a.attempt_id}>
            <span>{a.exam_title}</span>
            <span className="muted">{formatDate(a.created_at)}</span>
            <span className="grade-sm">{a.score10.toFixed(1)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
