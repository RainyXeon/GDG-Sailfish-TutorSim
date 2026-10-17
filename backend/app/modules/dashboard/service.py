"""Màn quản lý trung tâm: CHỈ ĐỌC dữ liệu qua hàm công khai của các module khác (không tự SELECT bảng của họ)."""
from app.modules.auth import list_users
from app.modules.exams import center_exam_stats, top_misconceptions_for_center
from app.modules.tutoring import sessions_overview, topic_stats, tutor_stats

STATUS_LABEL = {True: "Đang hoạt động", False: "Tạm nghỉ"}


def tutors_overview(q=None):
    """Bảng gia sư. q: tìm theo tên, tên đăng nhập hoặc mã (GS-0001), không phân biệt hoa thường."""
    rows = []
    for t in list_users("tutor"):
        st = tutor_stats(t["id"])
        rows.append({"tutor_id": t["id"], "name": t["name"], "username": t["username"], "code": t["code"],
                     "sessions_count": st["sessions_count"], "avg_total": st["avg_total"], "last_session": st["last_session"],
                     "total_minutes": st["total_minutes"], "active": st["active"], "status_label": STATUS_LABEL[st["active"]]})
    if q:
        k = q.strip().lower()
        rows = [r for r in rows if k in r["name"].lower() or k in r["username"].lower() or k in r["code"].lower()]
    return rows


def center_misconceptions(limit=10):
    return top_misconceptions_for_center(limit)


def overview():
    """Số liệu tổng cho màn Tổng quan / Thống kê."""
    tutors = tutors_overview()
    s = sessions_overview()
    e = center_exam_stats()
    top = top_misconceptions_for_center(10)
    total = sum(m["count"] for m in top) or 1
    return {"tutors_count": len(tutors), "active_tutors": sum(1 for t in tutors if t["active"]),
            "students_count": len(list_users("student")), **s,
            "attempts_count": e["attempts_count"], "students_with_attempts": e["students_with_attempts"],
            "misconception_count": e["misconception_count"],
            "top_tutors": sorted([t for t in tutors if t["avg_total"] is not None], key=lambda t: -t["avg_total"])[:5],
            "top_misconceptions": [{**m, "percent": round(m["count"] * 100 / total)} for m in top[:5]]}


def topics(chuyen_de=None):
    """Theo chuyên đề và theo dạng bài: số buổi luyện của gia sư, điểm TB, số gia sư + lượt lỗi của học sinh."""
    tut = {(t["chuyen_de"], t["dang_bai"]): t for t in topic_stats()}
    ex = {(t["chuyen_de"], t["dang_bai"]): t for t in center_exam_stats()["topics"]}
    out = []
    for key in sorted(set(tut) | set(ex), key=lambda k: (k[0], k[1] is not None, k[1] or "")):
        if chuyen_de and key[0] != chuyen_de:
            continue
        a, b = tut.get(key, {}), ex.get(key, {})
        out.append({"chuyen_de": key[0], "dang_bai": key[1], "label": a.get("label") or b.get("label"),
                    "sessions_count": a.get("sessions_count", 0), "avg_total": a.get("avg_total"),
                    "tutors_count": a.get("tutors_count", 0), "practiced_misconceptions": a.get("practiced_misconceptions", [])[:5],
                    "student_misconception_count": b.get("misconception_count", 0),
                    "student_top_misconceptions": b.get("top_misconceptions", [])})
    return out
