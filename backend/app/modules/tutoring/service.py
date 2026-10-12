"""Nghiệp vụ Phân hệ 1 (gia sư luyện với học sinh ảo). Bảng của module: sessions, messages, reports.
Nối bộ não (agent/) với database. Không phụ thuộc FastAPI -> test được bằng Python thường."""
import time

from agent import evaluator
from agent.classifier import classify
from agent.library import MISCONCEPTIONS, PERSONAS, RUBRIC_KEYS, topic_label
from agent.llm import LLMError
from agent.math_check import verify
from agent.simulator import student_reply
from agent.state_machine import DA_HIEU, KnowledgeState
from app.core import db
from app.core.errors import ServiceError
from app.modules.auth import get_user
from app.modules.coach import plan_next_for
from settings import settings

db.register_schema("tutoring", """
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, tutor_id INTEGER NOT NULL, chuyen_de TEXT NOT NULL,
  misconception_id TEXT NOT NULL, persona TEXT NOT NULL, state_json TEXT NOT NULL,
  coach_json TEXT, status TEXT NOT NULL DEFAULT 'in_progress', created_at TEXT NOT NULL, finished_at TEXT);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL, role TEXT NOT NULL,
  content TEXT NOT NULL, meta_json TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reports (
  session_id INTEGER PRIMARY KEY, scores_json TEXT NOT NULL, total REAL NOT NULL,
  evidence_json TEXT NOT NULL, feedback TEXT NOT NULL, next_json TEXT, created_at TEXT NOT NULL);
""")

STUDENT_NAME = "Nam"


# ---------- tra cứu ----------
def _tutor(tutor_id):
    t = get_user(tutor_id)
    if not t or t["role"] != "tutor":
        raise ServiceError(404, "Không tìm thấy gia sư")
    return t


def _session(session_id):
    s = db.one("SELECT * FROM sessions WHERE id = ?", (session_id,))
    if not s:
        raise ServiceError(404, "Không tìm thấy phiên")
    return s


def _messages(session_id):
    return db.q("SELECT role, content, meta_json, created_at FROM messages WHERE session_id = ? ORDER BY id", (session_id,))


def _topic(mid):
    m = MISCONCEPTIONS.get(mid)
    return topic_label(m) if m else mid


def _history(m, msgs, limit_turns=None):
    lines = [f"{STUDENT_NAME}: (nộp bài) {m['loi_giai_sai']}"]
    keep = msgs[-(limit_turns * 2):] if limit_turns else msgs
    if len(keep) < len(msgs):
        lines.append("(... lược bớt các lượt cũ ...)")
    for x in keep:
        lines.append(f"{'Gia sư' if x['role'] == 'tutor' else STUDENT_NAME}: {x['content']}")
    return "\n".join(lines)


def check_session_access(user, session_id):
    """Gia sư chỉ đụng được phiên của mình; quản lý xem được mọi phiên."""
    s = _session(session_id)
    if user["role"] != "manager" and s["tutor_id"] != user["id"]:
        raise ServiceError(403, "Đây không phải buổi luyện của bạn")
    return s


# ---------- hồ sơ gia sư ----------
def tutor_sessions(tutor_id):
    _tutor(tutor_id)
    rows = db.q("""SELECT s.id, s.misconception_id, s.created_at, r.total FROM sessions s
                   JOIN reports r ON r.session_id = s.id WHERE s.tutor_id = ? ORDER BY s.id DESC""", (tutor_id,))
    return [{"session_id": r["id"], "topic": _topic(r["misconception_id"]), "total": r["total"],
             "created_at": r["created_at"]} for r in rows]


def tutor_profile(tutor_id, last_n=3):
    reps = db.q("""SELECT r.scores_json FROM reports r JOIN sessions s ON s.id = r.session_id
                   WHERE s.tutor_id = ? ORDER BY r.session_id DESC LIMIT ?""", (tutor_id, last_n))
    scores = [db.loads(r["scores_json"]) for r in reps]
    avg = {k: round(sum(s[k] for s in scores) / len(scores), 2) for k in RUBRIC_KEYS} if scores else {}
    practiced = [r["misconception_id"] for r in db.q("SELECT DISTINCT misconception_id FROM sessions WHERE tutor_id = ?", (tutor_id,))]
    return {"avg_scores": avg, "practiced_misconceptions": practiced,
            "sessions": db.one("SELECT COUNT(*) AS n FROM reports r JOIN sessions s ON s.id = r.session_id WHERE s.tutor_id = ?",
                               (tutor_id,))["n"]}


def tutor_stats(tutor_id):
    """Cho Dashboard: số buổi đã chấm, điểm trung bình, ngày gần nhất."""
    reps = db.q("""SELECT r.total, r.created_at FROM reports r JOIN sessions s ON s.id = r.session_id
                   WHERE s.tutor_id = ? ORDER BY r.session_id""", (tutor_id,))
    avg = round(sum(r["total"] for r in reps) / len(reps), 1) if reps else None
    return {"sessions_count": len(reps), "avg_total": avg, "last_session": reps[-1]["created_at"][:10] if reps else None}


# ---------- một buổi luyện ----------
def start_session(tutor_id, chuyen_de="ham_so", misconception_id=None, persona=None):
    _tutor(tutor_id)
    if chuyen_de not in ("ham_so", "oxyz"):
        raise ServiceError(400, "chuyen_de phải là ham_so hoặc oxyz")
    if misconception_id and misconception_id not in MISCONCEPTIONS:
        raise ServiceError(400, f"Không có lỗi sai {misconception_id}")
    if persona and persona not in PERSONAS:
        raise ServiceError(400, f"Không có tính cách {persona}")
    plan = None
    if not misconception_id or not persona:
        plan = plan_next_for(tutor_id, chuyen_de, tutor_profile(tutor_id))
        chosen = [f"lỗi {misconception_id}" if misconception_id else "", f"tính cách {persona}" if persona else ""]
        if any(chosen):
            plan["user_override"] = "Người thử tự chọn " + ", ".join(c for c in chosen if c) + "; Coach chỉ chọn phần còn lại."
        misconception_id = misconception_id or plan["misconception_id"]
        persona = persona or plan["persona"]
    m = MISCONCEPTIONS[misconception_id]
    state = KnowledgeState(len(m["dieu_kien_hieu_ra"]), extra_turns=PERSONAS[persona]["extra_turns"])
    sid = db.run("""INSERT INTO sessions(tutor_id, chuyen_de, misconception_id, persona, state_json, coach_json, created_at)
                    VALUES (?,?,?,?,?,?,?)""", (tutor_id, m["chuyen_de"], misconception_id, persona,
                                                db.dumps(state.to_dict()), db.dumps(plan), db.now()))
    return {"session_id": sid, "student_name": STUDENT_NAME, "topic": topic_label(m), "problem": m["bai_toan"],
            "student_solution": m["loi_giai_sai"], "geogebra_commands": m["geogebra"]}


def send_message(session_id, content):
    content = (content or "").strip()
    if not content:
        raise ServiceError(400, "Tin nhắn trống")
    s = _session(session_id)
    if s["status"] == "finished":
        raise ServiceError(409, "Phiên đã kết thúc")
    m = MISCONCEPTIONS[s["misconception_id"]]
    persona = PERSONAS[s["persona"]]
    state = KnowledgeState.from_dict(db.loads(s["state_json"]))
    msgs = _messages(session_id)
    history = _history(m, msgs, settings.max_history_turns)
    t0 = time.time()
    try:
        c = classify(content, m, history)                      # LLM: gia sư đã đáp ứng điều kiện nào?
        math_ok, warnings = verify(c.math_claims)              # SymPy: gia sư nói toán có đúng không?
        before = state.state
        new_state = state.update(c.satisfied, tutor_math_ok=math_ok, gives_away=c.gives_away_answer)  # code quyết định
        reply = student_reply(m, persona, new_state, history + f"\nGia sư: {content}", STUDENT_NAME)  # LLM: Nam trả lời
    except LLMError as e:
        raise ServiceError(503, f"Học sinh ảo tạm thời không trả lời được: {e}")
    meta = {"satisfied_this_turn": c.satisfied, "gives_away": c.gives_away_answer, "reason": c.reason,
            "math_claims": [x.model_dump() for x in c.math_claims], "math_warnings": warnings,
            "state_before": before, "state_after": new_state, "satisfied_total": sorted(state.satisfied),
            "convincing_turns": state.convincing_turns, "turns_needed": state.turns_needed,
            "latency_ms": int((time.time() - t0) * 1000)}
    db.run("INSERT INTO messages(session_id, role, content, meta_json, created_at) VALUES (?,?,?,?,?)",
           (session_id, "tutor", content, db.dumps(meta), db.now()))
    db.run("INSERT INTO messages(session_id, role, content, meta_json, created_at) VALUES (?,?,?,?,?)",
           (session_id, "student", reply, None, db.now()))
    db.run("UPDATE sessions SET state_json = ? WHERE id = ?", (db.dumps(state.to_dict()), session_id))
    return {"student_reply": reply, "math_warnings": warnings,
            "status": "student_understood" if new_state == DA_HIEU else "in_progress"}


def finish_session(session_id):
    s = _session(session_id)
    if db.one("SELECT 1 AS x FROM reports WHERE session_id = ?", (session_id,)):
        return {"report_id": session_id}
    msgs = _messages(session_id)
    if not any(x["role"] == "tutor" for x in msgs):
        raise ServiceError(400, "Chưa có tin nhắn nào để chấm")
    m = MISCONCEPTIONS[s["misconception_id"]]
    state = KnowledgeState.from_dict(db.loads(s["state_json"]))
    warnings = [w for x in msgs if x["role"] == "tutor" for w in (db.loads(x["meta_json"], {}) or {}).get("math_warnings", [])]
    try:
        scores, total, evidence, feedback = evaluator.evaluate(_history(m, msgs), m, state.state, warnings)
    except LLMError as e:
        raise ServiceError(503, f"Chưa chấm được: {e}")
    db.run("UPDATE sessions SET status = 'finished', finished_at = ? WHERE id = ?", (db.now(), session_id))
    db.run("""INSERT INTO reports(session_id, scores_json, total, evidence_json, feedback, created_at)
              VALUES (?,?,?,?,?,?)""", (session_id, db.dumps(scores), total, db.dumps(evidence), feedback, db.now()))
    nxt = plan_next_for(s["tutor_id"], s["chuyen_de"], tutor_profile(s["tutor_id"]))
    db.run("UPDATE reports SET next_json = ? WHERE session_id = ?", (db.dumps(nxt), session_id))
    return {"report_id": session_id}


def get_report(report_id):
    r = db.one("SELECT * FROM reports WHERE session_id = ?", (report_id,))
    if not r:
        raise ServiceError(404, "Không tìm thấy báo cáo")
    s = _session(report_id)
    nxt = db.loads(r["next_json"], {}) or {}
    rec = ""
    if nxt.get("misconception_id"):
        nm = MISCONCEPTIONS.get(nxt["misconception_id"])
        rec = (f"{nm['dang_bai']}, lỗi {nxt['misconception_id']}. {nxt.get('reason', '')}").strip() if nm else nxt.get("reason", "")
    return {"report_id": report_id, "scores": db.loads(r["scores_json"]), "total": r["total"],
            "evidence": db.loads(r["evidence_json"], []), "feedback": r["feedback"], "next_recommendation": rec,
            "next_chuyen_de": s["chuyen_de"], "next_misconception_id": nxt.get("misconception_id"),
            "next_persona": nxt.get("persona")}


def session_debug(session_id):
    """CHỈ cho CLI khi phát triển (DEBUG=1): trạng thái ẩn mà web không được thấy."""
    if not settings.debug:
        raise ServiceError(404, "Debug đang tắt")
    s = _session(session_id)
    turns = [{"role": x["role"], "content": x["content"], **(db.loads(x["meta_json"], {}) or {})} for x in _messages(session_id)]
    return {"session_id": session_id, "misconception_id": s["misconception_id"], "persona": s["persona"],
            "conditions": MISCONCEPTIONS[s["misconception_id"]]["dieu_kien_hieu_ra"],
            "state": db.loads(s["state_json"]), "coach": db.loads(s["coach_json"]), "status": s["status"], "turns": turns}


# ---------- thư viện (chỉ đọc) ----------
def list_misconceptions(chuyen_de=None):
    return [{"id": m["id"], "chuyen_de": m["chuyen_de"], "dang_bai": m["dang_bai"], "ten_loi": m["ten_loi"],
             "trang_thai": m.get("trang_thai", "")} for m in MISCONCEPTIONS.values()
            if not chuyen_de or m["chuyen_de"] == chuyen_de]


def list_personas():
    return [{"id": k, "ten": v["ten"], "mo_ta": v["mo_ta"]} for k, v in PERSONAS.items()]
