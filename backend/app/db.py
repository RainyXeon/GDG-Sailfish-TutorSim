"""
LƯU TRỮ: SQLite (có sẵn trong Python, không cần cài, không cần tài khoản).
Đủ cho thí điểm probation. Muốn chuyển sang Supabase/Postgres sau này: chỉ sửa file này.
"""
import json
import sqlite3
import threading
from datetime import datetime

from settings import settings

_lock = threading.Lock()
_conn = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
  name TEXT NOT NULL, role TEXT NOT NULL CHECK (role IN ('tutor', 'student', 'manager')), created_at TEXT NOT NULL);
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
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, exam_id TEXT NOT NULL,
  exam_title TEXT NOT NULL, score10 REAL NOT NULL, correct INTEGER NOT NULL, total INTEGER NOT NULL,
  time_spent_sec INTEGER NOT NULL, results_json TEXT NOT NULL, created_at TEXT NOT NULL);
"""
# Tài khoản thử, chỉ tạo khi SEED_DEMO=1 (mật khẩu = DEMO_PASSWORD). TẮT khi deploy thật.
DEMO_USERS = [("minh", "Minh", "tutor"), ("lan", "Lan", "tutor"), ("tuan", "Tuấn", "tutor"),
              ("ha", "Hà", "student"), ("khoa", "Khoa", "student")]


def now():
    return datetime.now().isoformat(timespec="seconds")


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(settings.db_path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
        _seed(_conn)
        _conn.commit()
    return _conn


def _seed(c):
    from .security import hash_password  # import muộn để tránh vòng lặp
    wanted = []
    if settings.seed_demo:
        wanted += [(u, n, r, settings.demo_password) for u, n, r in DEMO_USERS]
    if settings.manager_username and settings.manager_password:
        wanted.append((settings.manager_username, "Quản lý trung tâm", "manager", settings.manager_password))
    for username, name, role, pw in wanted:
        if not c.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            c.execute("INSERT INTO users(username, password_hash, name, role, created_at) VALUES (?,?,?,?,?)",
                      (username, hash_password(pw), name, role, now()))


def reset(path):
    """Dùng cho test: trỏ sang database khác."""
    global _conn
    if _conn is not None:
        _conn.close()
    _conn = None
    settings.db_path = path


def q(sql, args=()):
    with _lock:
        return [dict(r) for r in conn().execute(sql, args).fetchall()]


def one(sql, args=()):
    rows = q(sql, args)
    return rows[0] if rows else None


def run(sql, args=()):
    with _lock:
        c = conn()
        cur = c.execute(sql, args)
        c.commit()
        return cur.lastrowid


def dumps(v):
    return json.dumps(v, ensure_ascii=False)


def loads(s, default=None):
    return json.loads(s) if s else default
