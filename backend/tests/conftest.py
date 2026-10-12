"""Test chạy KHÔNG cần API key: bật FAKE_LLM và dùng database tạm.
Tài khoản thử: minh=1, lan=2, tuan=3 (gia sư); ha=4, khoa=5 (học sinh); quanly=6 (quản lý)."""
import os
import sys
import tempfile
from pathlib import Path

os.environ["FAKE_LLM"] = "1"
os.environ["DEBUG"] = "1"
os.environ["JWT_SECRET"] = "test-secret-chi-dung-cho-test-0123456789abcdef"
os.environ["SEED_DEMO"] = "1"
os.environ["DEMO_PASSWORD"] = "demo1234"
os.environ["MANAGER_USERNAME"] = "quanly"
os.environ["MANAGER_PASSWORD"] = "quanly-mat-khau"
os.environ["DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test.sqlite3")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
