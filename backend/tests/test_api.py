"""Kiểm tra lớp API (cần fastapi + httpx: pip install -r requirements.txt)."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

c = TestClient(app)


def test_api_dung_hop_dong():
    assert c.get("/api/health").json()["fake_llm"] is True
    assert c.get("/api/tutors").json()[0]["name"] == "Minh"
    s = c.post("/api/sessions", json={"tutor_id": 1, "chuyen_de": "oxyz"}).json()
    assert {"session_id", "student_name", "topic", "problem", "student_solution", "geogebra_commands"} <= set(s)
    m = c.post(f"/api/sessions/{s['session_id']}/messages", json={"content": "Em kiểm tra lại công thức"}).json()
    assert m["status"] in ("in_progress", "student_understood")
    assert c.post(f"/api/sessions/{s['session_id']}/finish").json() == {"report_id": s["session_id"]}
    assert c.get(f"/api/reports/{s['session_id']}").status_code == 200
    assert c.get("/api/sessions/9999/debug").status_code == 404
    assert c.post("/api/attempts", json={"student_id": 1, "exam_id": "de-02", "answers": {"Q11": "B"}, "time_spent_sec": 60}).json()["results"][0]["misconception_id"] == "OX-01"
