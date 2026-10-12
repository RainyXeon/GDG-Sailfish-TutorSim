import { useEffect, useState } from "react";
import { getReport } from "../api.js";
import { CRITERIA } from "../constants.js";

export default function Report({ reportId, onAgain, onHome }) {
  const [r, setR] = useState(null);
  useEffect(() => { getReport(reportId).then(setR); }, [reportId]);
  if (!r) return <p className="muted center">Đang tải nhận xét…</p>;

  const nextCd = r.next_chuyen_de || "ham_so";

  return (
    <section className="report">
      <div className="report-head">
        <div className="grade" aria-label={`Điểm tổng ${r.total} trên 4`}>
          <span className="grade-num">{r.total.toFixed(1)}</span><span className="grade-of">/4</span>
        </div>
        <div>
          <h1 className="title">Nhận xét buổi chữa bài</h1>
          <p className="lead">{r.feedback}</p>
        </div>
      </div>

      <h2 className="h2">Theo từng tiêu chí</h2>
      <ul className="criteria">
        {Object.entries(CRITERIA).map(([key, label]) => (
          <li key={key}>
            <span className="crit-label">{label}</span>
            <span className="dots" aria-label={`${r.scores[key]} trên 4`}>
              {[1, 2, 3, 4].map((n) => <span key={n} className={n <= r.scores[key] ? "dot on" : "dot"} />)}
            </span>
          </li>
        ))}
      </ul>

      <h2 className="h2">Dẫn chứng từ buổi học</h2>
      <ul className="evidence">
        {r.evidence.map((e, i) => (
          <li key={i}>
            <p className="ev-crit">{CRITERIA[e.criterion]}</p>
            <blockquote>{e.quote}</blockquote>
            <p className="ev-note">{e.comment}</p>
          </li>
        ))}
      </ul>

      <div className="next">
        <p><strong>Buổi tiếp theo nên luyện:</strong> {r.next_recommendation}</p>
        <div className="row">
          <button className="btn primary" onClick={() => onAgain(nextCd, r.next_misconception_id, r.next_persona)}>Luyện theo gợi ý</button>
          <button className="btn" onClick={onHome}>Về trang chủ</button>
        </div>
      </div>
    </section>
  );
}
