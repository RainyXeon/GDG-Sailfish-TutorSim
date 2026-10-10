import { useEffect, useState } from "react";
import { getTutorSessions } from "../api.js";
import { formatDate } from "../constants.js";

export default function Home({ tutor, onStart }) {
  const [sessions, setSessions] = useState(null);
  const [chuyenDe, setChuyenDe] = useState("ham_so");

  useEffect(() => { getTutorSessions(tutor.id).then(setSessions); }, [tutor.id]);

  return (
    <section className="narrow">
      <h1 className="title">Chào {tutor.name}</h1>

      <div className="start-box">
        <h2 className="h2">Buổi luyện mới</h2>
        <div className="seg" role="radiogroup" aria-label="Chọn chuyên đề">
          {[["ham_so", "Hàm số"], ["oxyz", "Hình học Oxyz"]].map(([v, label]) => (
            <button key={v} role="radio" aria-checked={chuyenDe === v}
              className={chuyenDe === v ? "seg-item on" : "seg-item"} onClick={() => setChuyenDe(v)}>{label}</button>
          ))}
        </div>
        <button className="btn primary" onClick={() => onStart(chuyenDe)}>Bắt đầu chữa bài</button>
      </div>

      <h2 className="h2">Các buổi đã luyện</h2>
      {!sessions && <p className="muted">Đang tải…</p>}
      {sessions?.length === 0 && <p className="muted">Chưa có buổi nào. Bắt đầu buổi đầu tiên ở trên nhé.</p>}
      <ul className="history">
        {sessions?.map((s) => (
          <li key={s.session_id}>
            <span>{s.topic}</span>
            <span className="muted">{formatDate(s.created_at)}</span>
            <span className="grade-sm">{s.total.toFixed(1)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
