import { useEffect, useState } from "react";
import { getDashboard, getMisconceptionInsights } from "../api.js";

export default function Dashboard() {
  const [rows, setRows] = useState(null);
  const [mis, setMis] = useState(null);
  useEffect(() => { getDashboard().then(setRows); getMisconceptionInsights().then(setMis); }, []);

  return (
    <section>
      <h1 className="title">Bảng theo dõi gia sư</h1>
      <p className="lead">Điểm trung bình theo thang 4, tính từ các buổi luyện với học sinh ảo.</p>
      {!rows && <p className="muted">Đang tải…</p>}
      {rows && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Gia sư</th><th>Số buổi</th><th>Điểm trung bình</th><th>Buổi gần nhất</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.tutor_id}>
                  <td>{r.name}</td>
                  <td>{r.sessions_count}</td>
                  <td>
                    {r.avg_total == null ? <span className="muted">Chưa có</span> : (
                      <span className="bar-cell">
                        <span className="bar"><span style={{ width: `${(r.avg_total / 4) * 100}%` }} /></span>
                        {r.avg_total.toFixed(1)}
                      </span>
                    )}
                  </td>
                  <td>{r.last_session ?? "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h2 className="h2">Lỗi học sinh của trung tâm hay mắc</h2>
      <p className="lead">Lấy từ bài luyện đề của học sinh. Gia sư nên được luyện chữa đúng những lỗi này trước.</p>
      {mis?.length === 0 && <p className="muted">Chưa có dữ liệu bài làm.</p>}
      <ul className="mis-list wide">
        {mis?.map((m) => (
          <li key={m.id}><span><span className="mis-id">{m.id}</span>{m.name}</span><span className="mis-count">{m.count} lần</span></li>
        ))}
      </ul>
    </section>
  );
}
