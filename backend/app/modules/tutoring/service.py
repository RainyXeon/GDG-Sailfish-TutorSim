"""Nghiệp vụ Phân hệ 1 (gia sư luyện với học sinh ảo). Bảng của module: sessions, messages, reports.
Nối bộ não (agent/) với database. Không phụ thuộc FastAPI -> test được bằng Python thường."""
import concurrent.futures
import random
import threading
import time
from datetime import datetime, timedelta

from agent import evaluator
from agent.classifier import classify
from agent.library import MISCONCEPTIONS, PERSONAS, RUBRIC, RUBRIC_KEYS, TOPICS, topic_label
from agent.llm import LLMError
from agent.math_check import verify
from agent.simulator import student_reply
from agent.state_machine import DA_HIEU, KnowledgeState
from app.core import db
from app.core.errors import ServiceError
from app.modules.auth import get_user
from app.modules.coach import plan_next_for, plan_next_rule_for
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


def _persona(pid):
    return {"persona": pid, "persona_name": PERSONAS[pid]["ten"] if pid in PERSONAS else pid}


def _minutes(start, end):
    """Thời lượng (phút, làm tròn, tối thiểu 1) giữa hai mốc ISO; None nếu thiếu."""
    if not start or not end:
        return None
    try:
        return max(1, round((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() / 60))
    except ValueError:
        return None


ACTIVE_DAYS = 14  # có buổi luyện trong 14 ngày gần nhất = "Đang hoạt động", không thì "Tạm nghỉ"


def _active(last_iso):
    if not last_iso:
        return False
    try:
        return datetime.now() - datetime.fromisoformat(last_iso) <= timedelta(days=ACTIVE_DAYS)
    except ValueError:
        return False


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
def tutor_sessions(tutor_id, include_unfinished=False):
    """Mặc định: chỉ các buổi đã chấm (như cũ). include_unfinished=True: thêm buổi đang làm dở / đã hủy
    (total = null) để gia sư làm tiếp hoặc xem lại."""
    _tutor(tutor_id)
    rows = db.q("""SELECT s.id, s.misconception_id, s.chuyen_de, s.persona, s.created_at, s.finished_at, s.status, r.total
                   FROM sessions s LEFT JOIN reports r ON r.session_id = s.id WHERE s.tutor_id = ? ORDER BY s.id DESC""",
                (tutor_id,))
    if not include_unfinished:
        rows = [r for r in rows if r["total"] is not None]
    return [{"session_id": r["id"], "topic": _topic(r["misconception_id"]), "chuyen_de": r["chuyen_de"],
             "chuyen_de_name": TOPICS.get(r["chuyen_de"], r["chuyen_de"]), **_persona(r["persona"]),
             "total": r["total"], "status": "finished" if r["total"] is not None else r["status"],
             "duration_min": _minutes(r["created_at"], r["finished_at"]) if r["total"] is not None else None,
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
    """Cho Dashboard + trang chủ gia sư: số buổi đã chấm, điểm trung bình, ngày gần nhất,
    tổng thời gian luyện (phút), điểm trung bình từng tiêu chí, còn hoạt động không."""
    reps = db.q("""SELECT r.total, r.scores_json, r.created_at, s.created_at AS started, s.finished_at FROM reports r
                   JOIN sessions s ON s.id = r.session_id WHERE s.tutor_id = ? ORDER BY r.session_id""", (tutor_id,))
    avg = round(sum(r["total"] for r in reps) / len(reps), 1) if reps else None
    scores = [db.loads(r["scores_json"]) for r in reps]
    crit = {k: round(sum(s[k] for s in scores) / len(scores), 2) for k in RUBRIC_KEYS} if scores else {}
    last = reps[-1]["created_at"] if reps else None
    return {"sessions_count": len(reps), "avg_total": avg, "last_session": last[:10] if last else None,
            "total_minutes": sum(_minutes(r["started"], r["finished_at"]) or 0 for r in reps),
            "avg_scores": crit, "active": _active(last)}


def topic_stats():
    """Cho quản lý: theo từng chuyên đề và từng dạng bài -> số buổi đã chấm, điểm TB, số gia sư đã luyện."""
    rows = db.q("""SELECT s.tutor_id, s.chuyen_de, s.misconception_id, r.total FROM sessions s
                   JOIN reports r ON r.session_id = s.id""")
    agg = {}
    for r in rows:
        m = MISCONCEPTIONS.get(r["misconception_id"])
        dang_bai = m["dang_bai"] if m else "Khác"
        for key in ((r["chuyen_de"], None), (r["chuyen_de"], dang_bai)):
            a = agg.setdefault(key, {"n": 0, "sum": 0.0, "tutors": set(), "mis": {}})
            a["n"] += 1
            a["sum"] += r["total"]
            a["tutors"].add(r["tutor_id"])
            a["mis"][r["misconception_id"]] = a["mis"].get(r["misconception_id"], 0) + 1
    out = []
    for (cd, dang_bai), a in agg.items():
        out.append({"chuyen_de": cd, "dang_bai": dang_bai,
                    "label": f"{TOPICS.get(cd, cd)} – {dang_bai}" if dang_bai else TOPICS.get(cd, cd),
                    "sessions_count": a["n"], "avg_total": round(a["sum"] / a["n"], 2), "tutors_count": len(a["tutors"]),
                    "practiced_misconceptions": [{"id": k, "name": MISCONCEPTIONS[k]["ten_loi"] if k in MISCONCEPTIONS else k,
                                                  "count": v} for k, v in sorted(a["mis"].items(), key=lambda kv: -kv[1])]})
    return sorted(out, key=lambda x: (x["dang_bai"] is not None, -x["sessions_count"]))


def sessions_overview():
    """Cho quản lý: tổng số buổi (mọi trạng thái) và số buổi đã chấm."""
    rows = db.q("SELECT status, COUNT(*) AS n FROM sessions GROUP BY status")
    by = {r["status"]: r["n"] for r in rows}
    graded = db.one("SELECT COUNT(*) AS n, AVG(total) AS a FROM reports")
    return {"sessions_total": sum(by.values()), "sessions_finished": graded["n"], "sessions_in_progress": by.get("in_progress", 0),
            "sessions_abandoned": by.get("abandoned", 0), "avg_total": round(graded["a"], 2) if graded["a"] is not None else None}


def rubric():
    return [{"key": r["key"], "name": r["ten"], "weight": r["trong_so"], "levels": {str(k): v for k, v in r["muc"].items()}}
            for r in RUBRIC]


# ---------- một buổi luyện ----------
def start_session(tutor_id, chuyen_de="ham_so", misconception_id=None, persona=None):
    _tutor(tutor_id)
    if chuyen_de not in ("ham_so", "oxyz"):
        raise ServiceError(400, "chuyen_de phải là ham_so hoặc oxyz")
    if misconception_id and misconception_id not in MISCONCEPTIONS:
        raise ServiceError(400, f"Không có lỗi sai {misconception_id}")
    if persona and persona not in PERSONAS:
        raise ServiceError(400, f"Không có tính cách {persona}")
    # Tính cách: gia sư tự chọn; bỏ trống thì NGẪU NHIÊN (không để Coach chọn nữa).
    persona_random = not persona
    if persona_random:
        persona = random.choice(list(PERSONAS))
    # Lỗi sai: bỏ trống thì Coach Agent chọn (như cũ)
    plan = None
    if not misconception_id:
        plan = plan_next_for(tutor_id, chuyen_de, tutor_profile(tutor_id))
        plan["persona_used"] = persona
        plan["persona_random"] = persona_random
        misconception_id = plan["misconception_id"]
    m = MISCONCEPTIONS[misconception_id]
    state = KnowledgeState(len(m["dieu_kien_hieu_ra"]), extra_turns=PERSONAS[persona]["extra_turns"])
    sid = db.run("""INSERT INTO sessions(tutor_id, chuyen_de, misconception_id, persona, state_json, coach_json, created_at)
                    VALUES (?,?,?,?,?,?,?)""", (tutor_id, m["chuyen_de"], misconception_id, persona,
                                                db.dumps(state.to_dict()), db.dumps(plan), db.now()))
    return {"session_id": sid, "student_name": STUDENT_NAME, "topic": topic_label(m), "chuyen_de": m["chuyen_de"],
            "problem": m["bai_toan"], "student_solution": m["loi_giai_sai"], "geogebra_commands": m["geogebra"],
            **_persona(persona), "persona_random": persona_random}


# Mỗi phiên có một khóa: tin nhắn đang chờ Nam trả lời và nút "Kết thúc" không chạy chồng lên nhau
# (trước đây bấm Kết thúc khi Nam chưa trả lời xong -> 2 lời gọi Gemini cùng lúc, dễ dính 429/503,
# và bấm 2 lần -> chấm 2 lần, lần thứ hai lỗi 500 do trùng khóa bảng reports).
# Khóa nằm trong bộ nhớ -> đúng khi chạy 1 tiến trình (uvicorn mặc định, SQLite).
_locks_guard = threading.Lock()
_session_locks = {}
_coach_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="coach")
_coach_jobs = {}  # session_id -> Future của Coach Agent đang chạy ngầm


def _lock_for(session_id):
    with _locks_guard:
        return _session_locks.setdefault(session_id, threading.Lock())


def _llm_error(prefix, e):
    return ServiceError(503, f"{prefix}: {e}", retry_after=getattr(e, "retry_after", None))


def _check_open(s):
    if s["status"] == "finished":
        raise ServiceError(409, "Phiên đã kết thúc")
    if s["status"] == "abandoned":
        raise ServiceError(409, "Phiên đã bị hủy")


def send_message(session_id, content):
    content = (content or "").strip()
    if not content:
        raise ServiceError(400, "Tin nhắn trống")
    with _lock_for(session_id):
        s = _session(session_id)
        _check_open(s)
        m = MISCONCEPTIONS[s["misconception_id"]]
        persona = PERSONAS[s["persona"]]
        state = KnowledgeState.from_dict(db.loads(s["state_json"]))
        msgs = _messages(session_id)
        history = _history(m, msgs, settings.max_history_turns)
        t0 = time.time()
        # Cả lượt (phân loại + Nam trả lời) chung một ngân sách thời gian, để request không vượt giới hạn proxy
        deadline = time.monotonic() + settings.llm_call_budget_sec
        try:
            c = classify(content, m, history, budget_sec=settings.llm_call_budget_sec * 0.55)  # LLM: gia sư đáp ứng điều kiện nào?
            math_ok, warnings = verify(c.math_claims)              # SymPy: gia sư nói toán có đúng không?
            before = state.state
            new_state = state.update(c.satisfied, tutor_math_ok=math_ok, gives_away=c.gives_away_answer)  # code quyết định
            reply = student_reply(m, persona, new_state, history + f"\nGia sư: {content}", STUDENT_NAME,
                                  budget_sec=max(10, deadline - time.monotonic()))  # LLM: Nam trả lời
        except LLMError as e:
            raise _llm_error("Học sinh ảo tạm thời không trả lời được", e)
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


def _save_next(session_id, nxt):
    """Chỉ ghi nếu chưa có gợi ý: gợi ý đã hiện cho gia sư thì không đổi nữa."""
    db.run("UPDATE reports SET next_json = ? WHERE session_id = ? AND next_json IS NULL", (db.dumps(nxt), session_id))


def _run_coach(session_id, tutor_id, chuyen_de):
    try:
        nxt = plan_next_for(tutor_id, chuyen_de, tutor_profile(tutor_id))
    except Exception as e:  # plan_next_for đã tự dự phòng; đây chỉ là lưới an toàn cuối
        nxt = plan_next_rule_for(chuyen_de, tutor_profile(tutor_id))
        nxt["error"] = str(e)[:300]
    _save_next(session_id, nxt)


def finish_session(session_id):
    """Chấm điểm rồi trả về ngay. Coach Agent chọn bài tiếp theo chạy NGẦM (trước đây chạy nối tiếp,
    cộng thêm tới 45 giây vào request -> proxy cắt, trình duyệt nhận 502/504)."""
    with _lock_for(session_id):
        s = _session(session_id)
        if db.one("SELECT 1 AS x FROM reports WHERE session_id = ?", (session_id,)):
            return {"report_id": session_id}
        if s["status"] == "abandoned":
            raise ServiceError(409, "Phiên đã bị hủy, không chấm được")
        msgs = _messages(session_id)
        if not any(x["role"] == "tutor" for x in msgs):
            raise ServiceError(400, "Chưa có tin nhắn nào để chấm")
        m = MISCONCEPTIONS[s["misconception_id"]]
        state = KnowledgeState.from_dict(db.loads(s["state_json"]))
        warnings = [w for x in msgs if x["role"] == "tutor" for w in (db.loads(x["meta_json"], {}) or {}).get("math_warnings", [])]
        try:
            scores, total, evidence, feedback = evaluator.evaluate(_history(m, msgs), m, state.state, warnings,
                                                                   budget_sec=settings.llm_call_budget_sec,)
        except LLMError as e:
            raise _llm_error("Chưa chấm được", e)
        db.run("""INSERT OR IGNORE INTO reports(session_id, scores_json, total, evidence_json, feedback, created_at)
                  VALUES (?,?,?,?,?,?)""", (session_id, db.dumps(scores), total, db.dumps(evidence), feedback, db.now()))
        db.run("UPDATE sessions SET status = 'finished', finished_at = ? WHERE id = ?", (db.now(), session_id))
        _coach_jobs[session_id] = _coach_pool.submit(_run_coach, session_id, s["tutor_id"], s["chuyen_de"])
    return {"report_id": session_id}


def abandon_session(session_id):
    """Gia sư bấm "Bỏ buổi này": đánh dấu hủy, không chấm, không tính vào điểm."""
    with _lock_for(session_id):
        s = _session(session_id)
        if s["status"] == "finished":
            raise ServiceError(409, "Phiên đã kết thúc, không hủy được")
        if s["status"] != "abandoned":
            db.run("UPDATE sessions SET status = 'abandoned', finished_at = ? WHERE id = ?", (db.now(), session_id))
    return {"session_id": session_id, "status": "abandoned"}


def get_session(session_id):
    """Chi tiết một buổi: đề, bài làm của Nam, toàn bộ hội thoại, trạng thái. Dùng để làm tiếp buổi dở
    hoặc đọc lại hội thoại. KHÔNG trả trạng thái hiểu ẩn / tính cách / lỗi sai (giống hợp đồng cũ)."""
    s = _session(session_id)
    m = MISCONCEPTIONS[s["misconception_id"]]
    msgs = _messages(session_id)
    understood = KnowledgeState.from_dict(db.loads(s["state_json"])).state == DA_HIEU
    has_report = bool(db.one("SELECT 1 AS x FROM reports WHERE session_id = ?", (session_id,)))
    return {"session_id": session_id, "student_name": STUDENT_NAME, "topic": topic_label(m), "chuyen_de": s["chuyen_de"],
            **_persona(s["persona"]), "duration_min": _minutes(s["created_at"], s["finished_at"]),
            "problem": m["bai_toan"], "student_solution": m["loi_giai_sai"], "geogebra_commands": m["geogebra"],
            "status": s["status"], "student_understood": understood,
            "created_at": s["created_at"], "finished_at": s["finished_at"],
            "report_id": session_id if has_report else None,
            "messages": [{"role": x["role"], "content": x["content"], "created_at": x["created_at"],
                          "math_warnings": (db.loads(x["meta_json"], {}) or {}).get("math_warnings", [])
                          if x["role"] == "tutor" else []} for x in msgs]}


def get_report(report_id):
    r = db.one("SELECT * FROM reports WHERE session_id = ?", (report_id,))
    if not r:
        raise ServiceError(404, "Không tìm thấy báo cáo")
    s = _session(report_id)
    if not r["next_json"]:
        # Coach còn đang chạy ngầm: chờ một chút; quá lâu (hoặc server vừa khởi động lại) thì dùng luật dự phòng
        fut = _coach_jobs.get(report_id)
        if fut is not None:
            try:
                fut.result(timeout=settings.coach_wait_in_report_sec)
            except Exception:
                pass
        r = db.one("SELECT * FROM reports WHERE session_id = ?", (report_id,))
        if not r["next_json"]:
            fb = plan_next_rule_for(s["chuyen_de"], tutor_profile(s["tutor_id"]))
            fb["error"] = "Coach Agent chưa kịp trả lời, dùng luật dự phòng"
            _save_next(report_id, fb)
            r = db.one("SELECT * FROM reports WHERE session_id = ?", (report_id,))
    job = _coach_jobs.get(report_id)
    if job is not None and job.done():
        _coach_jobs.pop(report_id, None)   # dọn bộ nhớ
    nxt = db.loads(r["next_json"], {}) or {}
    rec = ""
    nm = MISCONCEPTIONS.get(nxt.get("misconception_id"))
    if nxt.get("misconception_id"):
        rec = (f"{nm['dang_bai']}, lỗi {nxt['misconception_id']}. {nxt.get('reason', '')}").strip() if nm else nxt.get("reason", "")
    scores = db.loads(r["scores_json"])
    evidence = db.loads(r["evidence_json"], [])
    criteria = [{"key": c["key"], "name": c["ten"], "weight": c["trong_so"], "score": scores.get(c["key"]),
                 "evidence": [e for e in evidence if e.get("criterion") == c["key"]]} for c in RUBRIC]
    m = MISCONCEPTIONS.get(s["misconception_id"])
    next_persona = nxt.get("persona")
    return {"report_id": report_id, "scores": scores, "total": r["total"],
            "evidence": evidence, "feedback": r["feedback"], "next_recommendation": rec,
            # chuyên đề lấy theo lỗi sai Coach gợi ý (trước đây lấy theo buổi vừa xong)
            "next_chuyen_de": nm["chuyen_de"] if nm else s["chuyen_de"],
            "next_misconception_id": nxt.get("misconception_id"), "next_persona": next_persona,
            # ---- thêm cho màn Báo cáo theo Figma ----
            "criteria": criteria, "chuyen_de": s["chuyen_de"], "topic": topic_label(m) if m else s["misconception_id"],
            **_persona(s["persona"]), "created_at": s["created_at"], "finished_at": s["finished_at"],
            "duration_min": _minutes(s["created_at"], s["finished_at"]),
            "next_topic": topic_label(nm) if nm else None,
            "next_persona_name": PERSONAS[next_persona]["ten"] if next_persona in PERSONAS else None,
            "next_reason": nxt.get("reason", ""), "next_source": nxt.get("source")}


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
