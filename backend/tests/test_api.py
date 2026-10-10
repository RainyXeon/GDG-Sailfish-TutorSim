"""Lớp API: đúng hợp đồng + phân quyền (cần fastapi, httpx: pip install -r requirements.txt)."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

c = TestClient(app)


def auth(username, password="demo1234"):
    r = c.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_chua_dang_nhap_thi_401():
    assert c.get("/api/health").status_code == 200                      # công khai
    assert c.get("/api/exams").status_code == 401
    assert c.post("/api/sessions", json={"chuyen_de": "ham_so"}).status_code == 401
    assert c.get("/api/exams", headers={"Authorization": "Bearer token-gia"}).status_code == 401


def test_dang_ky_qua_api():
    r = c.post("/api/auth/register", json={"username": "hs_moi", "password": "12345678", "name": "HS mới", "role": "student"})
    assert r.status_code == 200
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    assert c.get("/api/auth/me", headers=h).json()["username"] == "hs_moi"
    bad = c.post("/api/auth/register", json={"username": "x_quanly", "password": "12345678", "name": "X", "role": "manager"})
    assert bad.status_code == 422                                          # vai manager bị chặn ngay ở schema


def test_luong_gia_su_dung_hop_dong():
    h = auth("minh")
    s = c.post("/api/sessions", json={"chuyen_de": "oxyz"}, headers=h).json()
    assert {"session_id", "student_name", "topic", "problem", "student_solution", "geogebra_commands"} <= set(s)
    sid = s["session_id"]
    m = c.post(f"/api/sessions/{sid}/messages", json={"content": "Em kiểm tra lại công thức"}, headers=h).json()
    assert m["status"] in ("in_progress", "student_understood")
    assert c.get(f"/api/sessions/{sid}/debug", headers=h).status_code == 200
    assert c.post(f"/api/sessions/{sid}/finish", headers=h).json() == {"report_id": sid}
    assert c.get(f"/api/reports/{sid}", headers=h).status_code == 200
    me = c.get("/api/auth/me", headers=h).json()
    assert c.get(f"/api/tutors/{me['id']}/sessions", headers=h).json()[0]["session_id"] == sid

    # gia sư khác không xem / chat được buổi của Minh
    lan = auth("lan")
    assert c.get(f"/api/reports/{sid}", headers=lan).status_code == 403
    assert c.post(f"/api/sessions/{sid}/messages", json={"content": "x"}, headers=lan).status_code == 403
    assert c.get(f"/api/tutors/{me['id']}/sessions", headers=lan).status_code == 403
    # quản lý xem được
    ql = auth("quanly", "quanly-mat-khau")
    assert c.get(f"/api/reports/{sid}", headers=ql).status_code == 200


def test_phan_quyen_theo_vai():
    gs, hs, ql = auth("minh"), auth("ha"), auth("quanly", "quanly-mat-khau")
    assert c.get("/api/dashboard", headers=gs).status_code == 403
    assert c.get("/api/dashboard", headers=hs).status_code == 403
    assert c.get("/api/dashboard", headers=ql).status_code == 200
    assert c.get("/api/insights/misconceptions", headers=gs).status_code == 403
    assert c.post("/api/sessions", json={"chuyen_de": "ham_so"}, headers=hs).status_code == 403
    assert c.post("/api/attempts", json={"exam_id": "de-01", "answers": {}, "time_spent_sec": 1}, headers=gs).status_code == 403


def test_luong_hoc_sinh():
    hs = auth("ha")
    me = c.get("/api/auth/me", headers=hs).json()
    r = c.post("/api/attempts", json={"exam_id": "de-02", "answers": {"Q11": "B"}, "time_spent_sec": 60}, headers=hs).json()
    assert r["results"][0]["misconception_id"] == "OX-01"
    assert c.get(f"/api/students/{me['id']}/summary", headers=hs).status_code == 200
    khoa = auth("khoa")
    assert c.get(f"/api/students/{me['id']}/summary", headers=khoa).status_code == 403
