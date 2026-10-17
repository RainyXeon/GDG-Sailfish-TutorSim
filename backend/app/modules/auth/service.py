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
CREATE TABLE IF NOT EXISTS password_reset_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, created_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', resolved_at TEXT);
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


CODE_PREFIX = {"tutor": "GS", "student": "HV", "manager": "QL"}


def user_code(user):
    """Mã hiển thị, ví dụ gia sư id 1 -> GS-0001 (không lưu DB, suy ra từ id)."""
    return f"{CODE_PREFIX.get(user['role'], 'TK')}-{int(user['id']):04d}"


def _with_code(u):
    if u:
        u["code"] = user_code(u)
    return u


def get_user(user_id):
    return _with_code(db.one(f"SELECT {USER_FIELDS} FROM users WHERE id = ?", (user_id,)))


def list_users(role):
    """[{id, name}] như cũ, thêm username và code."""
    return [_with_code(u) for u in db.q("SELECT id, name, username, role FROM users WHERE role = ? ORDER BY id", (role,))]


def update_profile(user_id, name):
    name = (name or "").strip()
    if not name or len(name) > 60:
        raise ServiceError(400, "Cần nhập tên hiển thị (tối đa 60 ký tự)")
    db.run("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    return get_user(user_id)


def change_password(user_id, old_password, new_password):
    row = db.one("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    if not row or not verify_password(old_password or "", row["password_hash"]):
        raise ServiceError(400, "Mật khẩu hiện tại không đúng")
    if len(new_password or "") < 8:
        raise ServiceError(400, "Mật khẩu mới cần ít nhất 8 ký tự")
    db.run("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
    return {"ok": True}


FORGOT_MSG = "Nếu tên đăng nhập đúng, quản lý trung tâm sẽ nhận được yêu cầu và đặt lại mật khẩu cho bạn."


def request_password_reset(username):
    """Quên mật khẩu (không có email): ghi yêu cầu để quản lý xử lý. Luôn trả cùng một câu,
    không tiết lộ tên đăng nhập có tồn tại hay không."""
    row = db.one("SELECT id, role FROM users WHERE username = ?", ((username or "").strip().lower(),))
    if row and row["role"] != "manager" and not db.one(
            "SELECT 1 AS x FROM password_reset_requests WHERE user_id = ? AND status = 'pending'", (row["id"],)):
        db.run("INSERT INTO password_reset_requests(user_id, created_at) VALUES (?,?)", (row["id"], db.now()))
    return {"ok": True, "message": FORGOT_MSG}


def list_reset_requests():
    rows = db.q("""SELECT r.id, r.user_id, r.created_at, u.username, u.name, u.role FROM password_reset_requests r
                   JOIN users u ON u.id = r.user_id WHERE r.status = 'pending' ORDER BY r.id""")
    return [{"request_id": r["id"], "user_id": r["user_id"], "username": r["username"], "name": r["name"],
             "role": r["role"], "code": user_code({"id": r["user_id"], "role": r["role"]}), "created_at": r["created_at"]}
            for r in rows]


def reset_password(user_id, new_password):
    """Quản lý đặt mật khẩu mới cho gia sư / học sinh; đóng các yêu cầu đang chờ của người đó."""
    u = get_user(user_id)
    if not u:
        raise ServiceError(404, "Không tìm thấy tài khoản")
    if u["role"] == "manager":
        raise ServiceError(403, "Không đặt lại mật khẩu quản lý qua chức năng này")
    if len(new_password or "") < 8:
        raise ServiceError(400, "Mật khẩu mới cần ít nhất 8 ký tự")
    db.run("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
    db.run("UPDATE password_reset_requests SET status = 'done', resolved_at = ? WHERE user_id = ? AND status = 'pending'",
           (db.now(), user_id))
    return {"ok": True}


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
