"""Cấu hình chung, đọc từ biến môi trường / file backend/.env (xem .env.example ở gốc repo)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

BACKEND_DIR = Path(__file__).resolve().parent
REPO_DIR = BACKEND_DIR.parent
DATA_DIR = REPO_DIR / "data"


def _flag(name, default="0"):
    return os.getenv(name, default).strip() in ("1", "true", "True", "yes")


class Settings:
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    model_strong = os.getenv("GEMINI_MODEL_STRONG", "gemini-flash-latest")
    fake_llm = _flag("FAKE_LLM")
    debug = _flag("DEBUG", "1")
    only_approved = _flag("ONLY_APPROVED")
    db_path = os.getenv("DB_PATH") or str(BACKEND_DIR / "tutorsim.sqlite3")
    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
    max_history_turns = int(os.getenv("MAX_HISTORY_TURNS", "12"))  # giới hạn hội thoại gửi lên Gemini
    llm_timeout_sec = int(os.getenv("LLM_TIMEOUT_SEC", "60"))      # tối đa cho 1 lần gọi Gemini
    # Mức "suy nghĩ" của model: minimal | low | medium | high | off (= không gửi, để model tự quyết)
    thinking = os.getenv("GEMINI_THINKING", "minimal").strip().lower()
    thinking_strong = os.getenv("GEMINI_THINKING_STRONG", "medium").strip().lower()
    llm_retries = int(os.getenv("LLM_RETRIES", "3"))               # số lần thử khi Gemini lỗi
    # Tổng thời gian tối đa cho 1 lần "hỏi" Gemini, KỂ CẢ thử lại và thời gian chờ. Giữ dưới giới hạn của proxy
    # đứng trước backend (Render/nginx thường cắt ở 60-100 giây và trả 502/504).
    llm_call_budget_sec = int(os.getenv("LLM_CALL_BUDGET_SEC", "80"))
    llm_max_retry_wait_sec = int(os.getenv("LLM_MAX_RETRY_WAIT_SEC", "20"))  # chờ tối đa giữa 2 lần thử (lỗi 429)
    coach_budget_sec = int(os.getenv("COACH_BUDGET_SEC", "45"))    # Coach chậm hơn mức này -> dùng luật dự phòng
    # Coach chạy NGẦM sau khi chấm xong. Lúc mở báo cáo, chờ Coach tối đa bấy nhiêu giây rồi dùng luật dự phòng
    coach_wait_in_report_sec = int(os.getenv("COACH_WAIT_IN_REPORT_SEC", "15"))
    # ---- Đăng nhập ----
    jwt_secret = os.getenv("JWT_SECRET", "")
    jwt_expire_days = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
    allow_register = _flag("ALLOW_REGISTER", "1")      # cho gia sư, học sinh tự đăng ký
    seed_demo = _flag("SEED_DEMO", "1")                # tạo sẵn tài khoản thử (minh, lan, tuan, ha, khoa)
    demo_password = os.getenv("DEMO_PASSWORD", "demo1234")
    manager_username = os.getenv("MANAGER_USERNAME", "")
    manager_password = os.getenv("MANAGER_PASSWORD", "")


settings = Settings()

if not settings.jwt_secret:
    import secrets
    import warnings
    settings.jwt_secret = secrets.token_hex(32)
    warnings.warn("Chưa đặt JWT_SECRET: dùng khóa tạm, mọi người phải đăng nhập lại sau mỗi lần khởi động server.")
