"""Tài khoản: đăng ký, đăng nhập, tra cứu người dùng. Bảng: users."""
import re

from app.core import db
from app.core.errors import ServiceError
from app.core.security import create_token, hash_password, verify_password
from settings import settings

db.register_schema("auth", """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
  name TEXT NOT NULL, role TEXT NOT NULL CHECK (role IN ('tutor', 'student', 'manager')), created_at TEXT NOT NULL);
""")

# Tài khoản thử, chỉ tạo khi SEED_DEMO=1 (mật khẩu = DEMO_PASSWORD). TẮT khi deploy thật.
DEMO_USERS = [("minh", "Minh", "tutor"), ("lan", "Lan", "tutor"), ("tuan", "Tuấn", "tutor"),
              ("ha", "Hà", "student"), ("khoa", "Khoa", "student")]
USER_FIELDS = "id, username, name, role, created_at"
USERNAME_RE = re.compile(r"^[a-z0-9_.]{3,32}$")


@db.register_seed
def _seed(c):
    wanted = []
    if settings.seed_demo:
        wanted += [(u, n, r, settings.demo_password) for u, n, r in DEMO_USERS]
    if settings.manager_username and settings.manager_password:
        wanted.append((settings.manager_username, "Quản lý trung tâm", "manager", settings.manager_password))
    for username, name, role, pw in wanted:
        if not c.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            c.execute("INSERT INTO users(username, password_hash, name, role, created_at) VALUES (?,?,?,?,?)",
                      (username, hash_password(pw), name, role, db.now()))


def get_user(user_id):
    return db.one(f"SELECT {USER_FIELDS} FROM users WHERE id = ?", (user_id,))


def list_users(role):
    return db.q("SELECT id, name FROM users WHERE role = ? ORDER BY id", (role,))


def register(username, password, name, role):
    if not settings.allow_register:
        raise ServiceError(403, "Đang tắt tự đăng ký. Liên hệ quản lý trung tâm.")
    username = (username or "").strip().lower()
    name = (name or "").strip()
    if role not in ("tutor", "student"):
        raise ServiceError(400, "Chỉ tự đăng ký được vai gia sư (tutor) hoặc học sinh (student)")
    if not USERNAME_RE.match(username):
        raise ServiceError(400, "Tên đăng nhập 3–32 ký tự, chỉ gồm chữ thường không dấu, số, dấu chấm, gạch dưới")
    if len(password or "") < 8:
        raise ServiceError(400, "Mật khẩu cần ít nhất 8 ký tự")
    if not name or len(name) > 60:
        raise ServiceError(400, "Cần nhập tên hiển thị (tối đa 60 ký tự)")
    if db.one("SELECT 1 AS x FROM users WHERE username = ?", (username,)):
        raise ServiceError(409, "Tên đăng nhập đã có người dùng")
    uid = db.run("INSERT INTO users(username, password_hash, name, role, created_at) VALUES (?,?,?,?,?)",
                 (username, hash_password(password), name, role, db.now()))
    user = get_user(uid)
    return {"token": create_token(user), "user": user}


def login(username, password):
    row = db.one("SELECT * FROM users WHERE username = ?", ((username or "").strip().lower(),))
    if not row or not verify_password(password or "", row["password_hash"]):
        raise ServiceError(401, "Sai tên đăng nhập hoặc mật khẩu")
    user = get_user(row["id"])
    return {"token": create_token(user), "user": user}
