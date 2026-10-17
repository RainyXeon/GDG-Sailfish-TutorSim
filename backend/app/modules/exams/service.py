"""Nghiệp vụ Phân hệ 2 (học sinh luyện đề). Bảng của module: attempts."""
from agent.library import MISCONCEPTIONS, TOPICS
import time

from app.core import db
from app.core.errors import ServiceError
from app.core.security import sign, unsign
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


def _enrich(exam, results):
    """Thêm nội dung câu hỏi, chữ của đáp án, dạng bài, mô tả lỗi sai (để màn Kết quả hiển thị đủ như Figma).
    Tính lúc đọc, không lưu thêm vào DB -> bài cũ cũng có."""
    qs = {q["id"]: q for q in (exam or {}).get("questions", [])}
    out = []
    for r in results:
        q = qs.get(r["question_id"], {})
        opts = q.get("options", {})
        m = MISCONCEPTIONS.get(r.get("misconception_id"))
        out.append({**r, "content": q.get("content", ""), "options": opts, "dang_bai": q.get("dang_bai", ""),
                    "chosen_text": opts.get(r.get("chosen")) if r.get("chosen") else None,
                    "correct_text": opts.get(r.get("correct_answer")),
                    "misconception_description": m["nguyen_nhan_goc"] if m else None})
    return out


def _counts(results):
    wrong = sum(1 for r in results if not r["is_correct"] and r.get("chosen"))
    blank = sum(1 for r in results if not r.get("chosen"))
    mis = len({r["misconception_id"] for r in results if r.get("misconception_id")})
    return {"num_wrong": wrong, "num_blank": blank, "num_misconceptions": mis}


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


GRACE_SEC = 30  # cho phép trễ chút vì mạng / tự nộp khi hết giờ


def _late(exam, time_spent_sec):
    return time_spent_sec > exam["time_limit_min"] * 60 + GRACE_SEC


def start_attempt(student_id, exam_id):
    """Phát "vé làm bài" có ký, ghi giờ bắt đầu do SERVER đo. Gửi kèm khi nộp để server tự tính thời gian làm."""
    e = _exam(exam_id)
    limit = e["time_limit_min"] * 60
    token = sign({"typ": "exam", "sub": str(student_id), "exam": exam_id, "t0": time.time()}, limit + 6 * 3600)
    return {"attempt_token": token, "exam_id": exam_id, "time_limit_sec": limit}


def _server_time_spent(token, student_id, exam_id):
    d = unsign(token)
    if not d or d.get("typ") != "exam" or d.get("sub") != str(student_id) or d.get("exam") != exam_id:
        raise ServiceError(400, "Vé làm bài không hợp lệ hoặc đã hết hạn")
    return max(0, int(time.time() - float(d["t0"])))


def submit_attempt(student_id, exam_id, answers, time_spent_sec, attempt_token=None):
    u = get_user(student_id)
    if not u or u["role"] != "student":
        raise ServiceError(404, "Không tìm thấy học sinh")
    e = _exam(exam_id)
    # Mã câu không thuộc đề (ví dụ đề vừa được sửa lúc học sinh đang làm) thì bỏ qua, KHÔNG báo lỗi,
    # để học sinh không mất bài. grade() chỉ chấm các câu có trong đề.
    if attempt_token:   # có vé -> tin đồng hồ server, bỏ qua số giây trình duyệt gửi
        time_spent_sec = _server_time_spent(attempt_token, student_id, exam_id)
    time_spent_sec = max(0, int(time_spent_sec))
    g = grading.grade(e, answers)
    for r in g["results"]:
        if r["misconception_id"] in MISCONCEPTIONS:
            r["misconception_name"] = MISCONCEPTIONS[r["misconception_id"]]["ten_loi"]
    aid = db.run("""INSERT INTO attempts(student_id, exam_id, exam_title, score10, correct, total, time_spent_sec, results_json, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""", (student_id, exam_id, e["title"], g["score10"], g["correct"], g["total"],
                                                    time_spent_sec, db.dumps(g["results"]), db.now()))
    results = _enrich(e, g["results"])
    return {"attempt_id": aid, "exam_title": e["title"], "time_spent_sec": time_spent_sec,
            "late": _late(e, time_spent_sec), **g, "results": results, "exam_id": exam_id, **_counts(results)}


def get_attempt(attempt_id):
    """Chi tiết một bài đã nộp (xem lại từng câu). Trả về kèm student_id để router kiểm tra quyền."""
    r = db.one("SELECT * FROM attempts WHERE id = ?", (attempt_id,))
    if not r:
        raise ServiceError(404, "Không tìm thấy bài làm")
    e = grading.EXAMS.get(r["exam_id"])
    return {"attempt_id": r["id"], "student_id": r["student_id"], "exam_id": r["exam_id"], "exam_title": r["exam_title"],
            "correct": r["correct"], "total": r["total"], "score10": r["score10"], "time_spent_sec": r["time_spent_sec"],
            "late": _late(e, r["time_spent_sec"]) if e else False, "created_at": r["created_at"],
            "results": _enrich(e, db.loads(r["results_json"], [])), **_counts(db.loads(r["results_json"], []))}


def student_summary(student_id):
    rows = db.q("SELECT * FROM attempts WHERE student_id = ? ORDER BY id", (student_id,))
    top = _with_full_names(grading.top_misconceptions([db.loads(r["results_json"], []) for r in rows]))
    stats = {"attempts_count": len(rows), "exams_done": len({r["exam_id"] for r in rows}),
             "avg_score10": round(sum(r["score10"] for r in rows) / len(rows), 2) if rows else None}
    return {"attempts": [{"attempt_id": r["id"], "exam_id": r["exam_id"], "exam_title": r["exam_title"], "score10": r["score10"],
                          "correct": r["correct"], "total": r["total"], "time_spent_sec": r["time_spent_sec"],
                          "created_at": r["created_at"]} for r in reversed(rows)],
            "top_misconceptions": top, "prediction": grading.predict([r["score10"] for r in rows]),
            "note": PREDICT_NOTE, "stats": stats}


def top_misconceptions_for_center(limit=10):
    """Lỗi sai học sinh toàn trung tâm hay mắc nhất. Coach và Dashboard dùng hàm này."""
    lists = [db.loads(a["results_json"], []) for a in db.q("SELECT results_json FROM attempts")]
    return _with_full_names(grading.top_misconceptions(lists, limit))


def center_exam_stats():
    """Cho quản lý: số bài, số học sinh đã làm, tổng lượt lỗi sai, và lượt lỗi theo chuyên đề / dạng bài."""
    rows = db.q("SELECT student_id, results_json FROM attempts")
    by = {}
    total_mis = 0
    for a in rows:
        for r in db.loads(a["results_json"], []):
            mid = r.get("misconception_id")
            if not mid:
                continue
            total_mis += 1
            m = MISCONCEPTIONS.get(mid)
            cd = m["chuyen_de"] if m else ("oxyz" if mid.startswith("OX") else "ham_so")
            for key in ((cd, None), (cd, m["dang_bai"] if m else "Khác")):
                b = by.setdefault(key, {"count": 0, "mis": {}})
                b["count"] += 1
                b["mis"][mid] = b["mis"].get(mid, 0) + 1
    topics = [{"chuyen_de": cd, "dang_bai": db_, "label": f"{TOPICS.get(cd, cd)} – {db_}" if db_ else TOPICS.get(cd, cd),
               "misconception_count": b["count"],
               "top_misconceptions": _with_full_names([{"id": k, "name": grading.NAMES.get(k, k), "count": v}
                                                       for k, v in sorted(b["mis"].items(), key=lambda kv: -kv[1])[:5]])}
              for (cd, db_), b in by.items()]
    return {"attempts_count": len(rows), "students_with_attempts": len({a["student_id"] for a in rows}),
            "misconception_count": total_mis, "topics": topics}
