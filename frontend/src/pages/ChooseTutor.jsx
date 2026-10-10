import { useEffect, useState } from "react";
import { getTutors, getStudents } from "../api.js";

// Màn đầu tiên: chọn vai (gia sư / học sinh) và tên. MVP chưa có đăng nhập.
export default function ChooseTutor({ onPick, onPickStudent, onManager }) {
  const [tutors, setTutors] = useState(null);
  const [students, setStudents] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getTutors(), getStudents()])
      .then(([t, s]) => { setTutors(t); setStudents(s); })
      .catch(() => setError("Không tải được danh sách. Kiểm tra backend đã chạy chưa."));
  }, []);

  return (
    <section className="narrow">
      <h1 className="title">TutorSim</h1>
      <p className="lead">Gia sư luyện chữa bài với học sinh ảo. Học sinh luyện đề và theo dõi điểm dự kiến.</p>
      {error && <p className="error">{error}</p>}
      {!tutors && !error && <p className="muted">Đang tải…</p>}

      {tutors && (
        <>
          <h2 className="h2">Tôi là gia sư</h2>
          <div className="tutor-grid">
            {tutors.map((t) => (
              <button key={t.id} className="tutor-btn" onClick={() => onPick(t)}>
                <span className="avatar" aria-hidden="true">{t.name[0]}</span>{t.name}
              </button>
            ))}
          </div>
          <h2 className="h2">Tôi là học sinh</h2>
          <div className="tutor-grid">
            {students.map((s) => (
              <button key={s.id} className="tutor-btn" onClick={() => onPickStudent(s)}>
                <span className="avatar student" aria-hidden="true">{s.name[0]}</span>{s.name}
              </button>
            ))}
          </div>
        </>
      )}
      <button className="link manager" onClick={onManager}>Tôi là quản lý trung tâm, xem bảng theo dõi</button>
    </section>
  );
}
