"""
DATABASE DÙNG CHUNG: SQLite (có sẵn trong Python, không cần cài).
Mỗi module tự khai báo bảng của mình bằng register_schema(...) và (nếu cần) dữ liệu mẫu bằng register_seed(...).
Quy ước: module CHỈ đọc/ghi bảng của chính mình; cần dữ liệu module khác thì gọi hàm công khai của module đó.
Muốn chuyển sang Postgres (Supabase) sau này: chỉ sửa file này.
"""
import json
import sqlite3
import threading
from datetime import datetime

from settings import settings

_lock = threading.Lock()
_conn = None
_schemas = []   # (module, sql)
_seeds = []     # hàm nhận connection


def register_schema(module, sql):
    _schemas.append((module, sql))
    if _conn is not None:          # module nạp muộn (sau khi đã mở database) -> tạo bảng ngay
        _conn.executescript(sql)


def register_seed(fn):
    _seeds.append(fn)
    return fn


def now():
    return datetime.now().isoformat(timespec="seconds")


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(settings.db_path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        for _, sql in _schemas:
            _conn.executescript(sql)
        for fn in _seeds:
            fn(_conn)
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
