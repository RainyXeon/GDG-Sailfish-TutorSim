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
CREATE TABLE IF NOT EXISTS tutors   (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
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
SEED_TUTORS = ["Minh", "Lan", "Tuấn"]
SEED_STUDENTS = ["Hà", "Khoa"]


def now():
    return datetime.now().isoformat(timespec="seconds")


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(settings.db_path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
        if not _conn.execute("SELECT 1 FROM tutors LIMIT 1").fetchone():
            _conn.executemany("INSERT INTO tutors(name) VALUES (?)", [(n,) for n in SEED_TUTORS])
            _conn.executemany("INSERT INTO students(name) VALUES (?)", [(n,) for n in SEED_STUDENTS])
        _conn.commit()
    return _conn


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
