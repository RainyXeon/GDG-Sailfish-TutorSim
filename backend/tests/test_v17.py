"""v1.7: chọn tính cách (bỏ trống = ngẫu nhiên), dữ liệu cho các màn Figma, tài khoản, quản lý. Không cần API key."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from agent.library import PERSONAS, RUBRIC  # noqa: E402
from app.main import app  # noqa: E402

c = TestClient(app)


def auth(username, password="demo1234"):
    r = c.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def manager():
    return auth("quanly", "quanly-mat-khau")


def run_session(h, cd="ham_so", persona=None):
    body = {"chuyen_de": cd}
    if persona:
        body["persona"] = persona
    s = c.post("/api/sessions", json=body, headers=h).json()
    c.post(f"/api/sessions/{s['session_id']}/messages", json={"content": "Em xét dấu y' hai bên xem"}, headers=h)
    c.post(f"/api/sessions/{s['session_id']}/finish", headers=h)
    return s


# ---------------- tính cách ----------------
def test_chon_tinh_cach():
    h = auth("minh")
    s = c.post("/api/sessions", json={"chuyen_de": "ham_so", "persona": "hay_cai"}, headers=h).json()
    assert s["persona"] == "hay_cai" and s["persona_name"] == "Hay cãi" and s["persona_random"] is False
    assert c.post("/api/sessions", json={"chuyen_de": "ham_so", "persona": "khong_co"}, headers=h).status_code == 400


def test_khong_chon_tinh_cach_thi_ngau_nhien():
    h = auth("minh")
    seen = set()
    for _ in range(25):
        s = c.post("/api/sessions", json={"chuyen_de": "oxyz"}, headers=h).json()
        assert s["persona_random"] is True and s["persona"] in PERSONAS
        seen.add(s["persona"])
        c.post(f"/api/sessions/{s['session_id']}/abandon", headers=h)
    assert len(seen) >= 2                                                   # thật sự ngẫu nhiên


# ---------------- báo cáo, lịch sử, thống kê gia sư ----------------
def test_bao_cao_theo_tieu_chi_backend():
    h = auth("lan")
    s = run_session(h, persona="mat_goc")
    r = c.get(f"/api/reports/{s['session_id']}", headers=h).json()
    assert [x["name"] for x in r["criteria"]] == [x["ten"] for x in RUBRIC]
    assert all(isinstance(x["score"], int) and 1 <= x["score"] <= 4 for x in r["criteria"])
    assert r["persona"] == "mat_goc" and r["persona_name"] == "Mất gốc" and r["duration_min"] >= 1
    assert r["topic"].startswith("Hàm số – ") and r["next_topic"] and r["next_persona_name"] and r["next_reason"]
    rub = c.get("/api/rubric", headers=h).json()
    assert [x["key"] for x in rub] == ["chinh_xac", "chan_doan", "ro_rang", "goi_mo", "thai_do"]


def test_lich_su_va_thong_ke_gia_su():
    h = auth("tuan")
    run_session(h, "oxyz", "thu_dong")
    me = c.get("/api/auth/me", headers=h).json()
    assert me["code"] == f"GS-{me['id']:04d}"
    hist = c.get(f"/api/tutors/{me['id']}/sessions", headers=h).json()
    assert hist[0]["persona_name"] == "Thụ động" and hist[0]["chuyen_de_name"] == "Hình học Oxyz" and hist[0]["duration_min"]
    st = c.get(f"/api/tutors/{me['id']}/stats", headers=h).json()
    assert st["sessions_count"] >= 1 and st["total_minutes"] >= 1 and st["active"] is True
    assert set(st["avg_scores"]) == {"chinh_xac", "chan_doan", "ro_rang", "goi_mo", "thai_do"}
    assert c.get(f"/api/tutors/{me['id']}/stats", headers=auth("lan")).status_code == 403
    assert c.get(f"/api/tutors/{me['id']}/stats", headers=manager()).status_code == 200


# ---------------- tài khoản ----------------
def test_doi_ten_doi_mat_khau():
    r = c.post("/api/auth/register", json={"username": "gs_doi", "password": "matkhau01", "name": "A", "role": "tutor"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    assert c.patch("/api/auth/me", json={"name": "Thầy Thành"}, headers=h).json()["name"] == "Thầy Thành"
    assert c.post("/api/auth/change-password", json={"old_password": "sai-roi-1", "new_password": "matkhau02"},
                  headers=h).status_code == 400
    assert c.post("/api/auth/change-password", json={"old_password": "matkhau01", "new_password": "matkhau02"},
                  headers=h).json()["ok"] is True
    assert c.post("/api/auth/login", json={"username": "gs_doi", "password": "matkhau02"}).status_code == 200


def test_quen_mat_khau_qua_quan_ly():
    c.post("/api/auth/register", json={"username": "hs_quen", "password": "matkhau01", "name": "B", "role": "student"})
    a = c.post("/api/auth/forgot-password", json={"username": "hs_quen"}).json()
    b = c.post("/api/auth/forgot-password", json={"username": "khong_ton_tai"}).json()
    assert a == b and a["ok"]                                              # không lộ tài khoản có tồn tại hay không
    ql = manager()
    reqs = c.get("/api/auth/reset-requests", headers=ql).json()
    req = next(x for x in reqs if x["username"] == "hs_quen")
    assert c.get("/api/auth/reset-requests", headers=auth("minh")).status_code == 403
    assert c.post(f"/api/users/{req['user_id']}/reset-password", json={"new_password": "moi-12345"}, headers=ql).json()["ok"]
    assert c.post("/api/auth/login", json={"username": "hs_quen", "password": "moi-12345"}).status_code == 200
    assert all(x["username"] != "hs_quen" for x in c.get("/api/auth/reset-requests", headers=ql).json())


# ---------------- học sinh ----------------
def test_ket_qua_bai_thi_day_du():
    hs = auth("ha")
    exam = c.get("/api/exams/de-01", headers=hs).json()
    assert {"dang_bai", "geogebra_commands"} <= set(exam["questions"][0])
    r = c.post("/api/attempts", json={"exam_id": "de-01", "answers": {"Q01": "A", "Q02": "B"}, "time_spent_sec": 100},
               headers=hs).json()
    q1, q2 = r["results"][0], r["results"][1]
    assert q1["content"] and q1["correct_text"] is not None and q1["dang_bai"]
    assert q2["chosen_text"] is not None and q2["misconception_id"] and q2["misconception_description"]
    assert r["num_wrong"] >= 1 and r["num_blank"] == 8 and r["num_misconceptions"] >= 1
    assert c.get(f"/api/attempts/{r['attempt_id']}", headers=hs).json()["results"][0]["content"] == q1["content"]
    me = c.get("/api/auth/me", headers=hs).json()
    st = c.get(f"/api/students/{me['id']}/summary", headers=hs).json()["stats"]
    assert st["attempts_count"] >= 1 and st["exams_done"] >= 1


# ---------------- quản lý ----------------
def test_quan_ly_tong_quan_tim_kiem_chu_de():
    run_session(auth("minh"), "ham_so", "hay_cai")
    ql = manager()
    ov = c.get("/api/dashboard/overview", headers=ql).json()
    assert ov["tutors_count"] >= 3 and ov["sessions_finished"] >= 1 and ov["active_tutors"] >= 1
    assert all("percent" in m for m in ov["top_misconceptions"])
    rows = c.get("/api/dashboard?q=gs-0001", headers=ql).json()
    assert len(rows) == 1 and rows[0]["code"] == "GS-0001" and rows[0]["status_label"] in ("Đang hoạt động", "Tạm nghỉ")
    assert c.get("/api/dashboard?q=minh", headers=ql).json()[0]["username"] == "minh"
    assert c.get("/api/dashboard?q=khong-ai-ca", headers=ql).json() == []
    tp = c.get("/api/dashboard/topics?chuyen_de=ham_so", headers=ql).json()
    assert tp[0]["dang_bai"] is None and tp[0]["label"] == "Hàm số"                # dòng tổng chuyên đề
    assert any(t["dang_bai"] and t["label"].startswith("Hàm số – ") for t in tp)  # dòng theo dạng bài
    assert c.get("/api/dashboard/overview", headers=auth("minh")).status_code == 403
