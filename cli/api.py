"""
GỌI REST API TutorSim - gom vào 1 chỗ
Chỉ dùng thư viện chuẩn (urllib), không cần pip install.
- Địa chỉ server: biến môi trường TUTORSIM_API_URL (mặc định http://127.0.0.1:8000)
- Đăng nhập: TUTORSIM_USER / TUTORSIM_PASSWORD, nếu không có thì hỏi trong terminal.
  Token được lưu vào cli/.token để lần sau không phải đăng nhập lại.
"""
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = os.getenv("TUTORSIM_API_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN_FILE = Path(__file__).parent / ".token"
TIMEOUT = 120  # lượt chat gọi Gemini 2 lần (phân loại + học sinh ảo), chấm điểm có thể lâu


class ApiError(Exception):
    def __init__(self, status, detail):
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.detail = detail


def _request(method, path, body=None, token=None):
    req = urllib.request.Request(BASE_URL + path, method=method)
    req.add_header("Accept", "application/json")
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("detail", e.reason)
        except Exception:
            detail = e.reason
        raise ApiError(e.code, detail) from None
    except urllib.error.URLError as e:
        sys.exit(f"Không kết nối được tới {BASE_URL} ({e.reason}).\n"
                 f"Hãy chạy server trước: cd rest_api && uvicorn main:app --reload")


def _ask_credentials():
    user = os.getenv("TUTORSIM_USER") or input("Tên đăng nhập: ").strip()
    password = os.getenv("TUTORSIM_PASSWORD") or getpass.getpass("Mật khẩu: ")
    return user, password


def login():
    """Đăng nhập (tạo tài khoản nếu chưa có) và lưu token."""
    user, password = _ask_credentials()
    try:
        token = _request("POST", "/auth/login", {"username": user, "password": password})["access_token"]
    except ApiError as e:
        if e.status != 401:
            raise
        ans = input(f"Đăng nhập thất bại. Tạo tài khoản mới '{user}'? (y/N): ").strip().lower()
        if ans != "y":
            sys.exit("Đã hủy.")
        _request("POST", "/auth/register", {"username": user, "password": password})
        token = _request("POST", "/auth/login", {"username": user, "password": password})["access_token"]
    TOKEN_FILE.write_text(token, encoding="utf-8")
    return token


def logout():
    TOKEN_FILE.unlink(missing_ok=True)


class Client:
    """Gọi API kèm token; token hết hạn thì tự đăng nhập lại 1 lần."""

    def __init__(self):
        self.token = TOKEN_FILE.read_text(encoding="utf-8").strip() if TOKEN_FILE.exists() else None
        if not self.token:
            self.token = login()

    def call(self, method, path, body=None):
        try:
            return _request(method, path, body, self.token)
        except ApiError as e:
            if e.status != 401:
                raise
            print("(Phiên đăng nhập hết hạn, đăng nhập lại)")
            self.token = login()
            return _request(method, path, body, self.token)

    # --- các endpoint ---
    def me(self):
        return self.call("GET", "/auth/me")

    def misconceptions(self):
        return self.call("GET", "/catalog/misconceptions")

    def personas(self):
        return self.call("GET", "/catalog/personas")

    def start_session(self, misconception_id, persona_key, intent, student_name):
        return self.call("POST", "/sessions", {"misconception_id": misconception_id, "persona_key": persona_key,
                                               "intent": intent, "student_name": student_name})

    def session(self, session_id):
        return self.call("GET", f"/sessions/{session_id}")

    def sessions(self):
        return self.call("GET", "/sessions")

    def add_turn(self, session_id, tutor_message):
        return self.call("POST", f"/sessions/{session_id}/turns", {"tutor_message": tutor_message})

    def finish(self, session_id):
        return self.call("POST", f"/sessions/{session_id}/finish")

    def gate(self):
        return self.call("GET", "/reports/gate")
