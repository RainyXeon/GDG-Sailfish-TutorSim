"""Test chạy KHÔNG cần API key: bật FAKE_LLM và dùng database tạm."""
import os
import sys
import tempfile
from pathlib import Path

os.environ["FAKE_LLM"] = "1"
os.environ["DEBUG"] = "1"
os.environ["DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test.sqlite3")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
