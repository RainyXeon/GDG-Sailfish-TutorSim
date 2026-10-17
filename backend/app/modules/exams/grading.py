"""Phần TÍNH TOÁN THUẦN của Phân hệ 2: nạp đề, chấm, dự đoán điểm, đếm lỗi. Không đụng database, không dùng LLM."""
import json
from statistics import pstdev

from settings import DATA_DIR


def load_exams():
    exams = {}
    for p in sorted((DATA_DIR / "exams").glob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        exams[e["id"]] = e
    return exams


EXAMS = load_exams()
NAMES = {k: v for e in EXAMS.values() for k, v in e.get("misconception_names", {}).items()}


def public_exam(exam):
    """Bản đề gửi cho học sinh: KHÔNG có đáp án, mã lỗi, lời giải."""
    return {"id": exam["id"], "title": exam["title"], "time_limit_min": exam["time_limit_min"],
            "questions": [{"id": q["id"], "content": q["content"], "options": q["options"], "dang_bai": q.get("dang_bai", ""),
                           "geogebra_commands": q.get("geogebra", [])} for q in exam["questions"]]}


def grade(exam, answers):
    results, correct = [], 0
    for q in exam["questions"]:
        chosen = answers.get(q["id"])
        ok = chosen == q["answer"]
        correct += ok
        mis = None if ok or chosen is None else q["misconceptions"].get(chosen)
        results.append({"question_id": q["id"], "chosen": chosen, "correct_answer": q["answer"], "is_correct": ok,
                        "misconception_id": mis, "misconception_name": NAMES.get(mis) if mis else None,
                        "explanation": q["explanation"]})
    total = len(exam["questions"])
    return {"correct": correct, "total": total, "score10": round(correct / total * 10, 2), "results": results}


def predict(scores10):
    """Trung bình có trọng số 3 bài gần nhất (1, 2, 3); khoảng = độ lệch chuẩn, tối thiểu 0,5. Cần >= 2 bài."""
    if len(scores10) < 2:
        return None
    last = scores10[-3:]
    w = list(range(1, len(last) + 1))
    mid = sum(s * k for s, k in zip(last, w)) / sum(w)
    spread = max(0.5, pstdev(last))
    return {"low": round(max(0, mid - spread), 1), "mid": round(mid, 1), "high": round(min(10, mid + spread), 1)}


def top_misconceptions(results_lists, limit=5):
    count = {}
    for results in results_lists:
        for r in results:
            if r.get("misconception_id"):
                count[r["misconception_id"]] = count.get(r["misconception_id"], 0) + 1
    ranked = sorted(count.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [{"id": k, "name": NAMES.get(k, k), "count": v} for k, v in ranked]
