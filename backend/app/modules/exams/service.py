"""Nghiệp vụ Phân hệ 2 (học sinh luyện đề). Bảng của module: attempts."""
from agent.library import MISCONCEPTIONS
from app.core import db
from app.core.errors import ServiceError
from app.modules.auth import get_user

from . import grading

db.register_schema("exams", """
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, exam_id TEXT NOT NULL,
  exam_title TEXT NOT NULL, score10 REAL NOT NULL, correct INTEGER NOT NULL, total INTEGER NOT NULL,
  time_spent_sec INTEGER NOT NULL, results_json TEXT NOT NULL, created_at TEXT NOT NULL);
""")

PREDICT_NOTE = "Ước lượng điểm môn Toán (chỉ 2 chuyên đề Hàm số, Oxyz) từ các bài luyện gần nhất, không phải cam kết."


def _with_full_names(top):
    """Tên đầy đủ lấy từ thư viện lỗi sai (agent/library) nếu có."""
    for t in top:
        if t["id"] in MISCONCEPTIONS:
            t["name"] = MISCONCEPTIONS[t["id"]]["ten_loi"]
    return top


def list_exams():
    return [{"id": e["id"], "title": e["title"], "chuyen_de": e["chuyen_de"], "num_questions": len(e["questions"]),
             "time_limit_min": e["time_limit_min"]} for e in grading.EXAMS.values()]


def _exam(exam_id):
    e = grading.EXAMS.get(exam_id)
    if not e:
        raise ServiceError(404, "Không tìm thấy đề")
    return e


def get_exam(exam_id):
    return grading.public_exam(_exam(exam_id))


def submit_attempt(student_id, exam_id, answers, time_spent_sec):
    u = get_user(student_id)
    if not u or u["role"] != "student":
        raise ServiceError(404, "Không tìm thấy học sinh")
    e = _exam(exam_id)
    g = grading.grade(e, answers)
    for r in g["results"]:
        if r["misconception_id"] in MISCONCEPTIONS:
            r["misconception_name"] = MISCONCEPTIONS[r["misconception_id"]]["ten_loi"]
    aid = db.run("""INSERT INTO attempts(student_id, exam_id, exam_title, score10, correct, total, time_spent_sec, results_json, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""", (student_id, exam_id, e["title"], g["score10"], g["correct"], g["total"],
                                                    int(time_spent_sec), db.dumps(g["results"]), db.now()))
    return {"attempt_id": aid, "exam_title": e["title"], "time_spent_sec": int(time_spent_sec), **g}


def student_summary(student_id):
    rows = db.q("SELECT * FROM attempts WHERE student_id = ? ORDER BY id", (student_id,))
    top = _with_full_names(grading.top_misconceptions([db.loads(r["results_json"], []) for r in rows]))
    return {"attempts": [{"attempt_id": r["id"], "exam_title": r["exam_title"], "score10": r["score10"],
                          "created_at": r["created_at"]} for r in reversed(rows)],
            "top_misconceptions": top, "prediction": grading.predict([r["score10"] for r in rows]),
            "note": PREDICT_NOTE}


def top_misconceptions_for_center(limit=10):
    """Lỗi sai học sinh toàn trung tâm hay mắc nhất. Coach và Dashboard dùng hàm này."""
    lists = [db.loads(a["results_json"], []) for a in db.q("SELECT results_json FROM attempts")]
    return _with_full_names(grading.top_misconceptions(lists, limit))
