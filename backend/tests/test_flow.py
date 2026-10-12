"""Đi hết luồng nghiệp vụ ở chế độ FAKE_LLM (không cần mạng, không cần key)."""
import pytest
import app.main  # noqa: F401  (nạp đủ các module + bảng)
from app.core.errors import ServiceError
from app.modules import dashboard, exams, tutoring
from agent.library import MISCONCEPTIONS


def test_du_lieu_nap_du():
    assert len(MISCONCEPTIONS) >= 50
    assert all(len(m["dieu_kien_hieu_ra"]) >= 2 for m in MISCONCEPTIONS.values())


def test_phien_luyen_tap_tu_dau_den_cuoi():
    s = tutoring.start_session(1, "ham_so", misconception_id="HS-01", persona="hay_cai")
    sid = s["session_id"]
    assert s["student_solution"] and s["geogebra_commands"] == ["f(x) = x^3 - 3"]
    r = tutoring.send_message(sid, "Em xem lại đi")                      # mơ hồ -> chưa tiến bộ
    assert r["status"] == "in_progress"
    assert tutoring.session_debug(sid)["state"]["state"] == "chua_nhan_ra"
    for _ in range(2):
        assert tutoring.send_message(sid, "y' = 0 chỉ là điều kiện cần, em xét xem y' có đổi dấu không")["status"] == "in_progress"
    r = tutoring.send_message(sid, "Vậy điều kiện cần chưa đủ, y' không đổi dấu thì sao?")  # hay cãi cần 3 lượt
    assert r["status"] == "student_understood"
    tutoring.finish_session(sid)
    rep = tutoring.get_report(sid)
    assert set(rep["scores"]) == {"chinh_xac", "chan_doan", "ro_rang", "goi_mo", "thai_do"}
    assert 1 <= rep["total"] <= 4 and rep["next_recommendation"]
    assert tutoring.tutor_sessions(1)[0]["session_id"] == sid
    with pytest.raises(ServiceError):
        tutoring.send_message(sid, "còn nữa không")                       # phiên đã kết thúc


def test_coach_tu_chon_va_uu_tien_loi_hoc_sinh_that():
    # học sinh làm đề: chọn B ở Q02 -> lỗi HS-07
    res = exams.submit_attempt(4, "de-01", {"Q02": "B"}, 300)            # học sinh Hà
    assert any(r["misconception_id"] == "HS-07" for r in res["results"])
    assert exams.top_misconceptions_for_center()[0]["id"] == "HS-07"
    s = tutoring.start_session(2, "ham_so")                                # gia sư Lan, không chỉ định -> Coach chọn
    dbg = tutoring.session_debug(s["session_id"])
    assert dbg["misconception_id"] == "HS-07" and dbg["persona"] == "thu_dong"
    assert dbg["coach"]["source"] == "rule" and dbg["coach"]["reason"]


def test_phan_he_2_du_doan():
    assert exams.student_summary(5)["prediction"] is None             # học sinh Khoa
    exams.submit_attempt(5, "de-01", {f"Q{i:02d}": "A" for i in range(1, 11)}, 600)   # đáp án đúng đều là A
    exams.submit_attempt(5, "de-02", {}, 600)
    summ = exams.student_summary(5)
    assert [a["score10"] for a in summ["attempts"]] == [0.0, 10.0]
    p = summ["prediction"]
    assert p["low"] <= p["mid"] <= p["high"]
    assert "Q01" in [q["id"] for q in exams.get_exam("de-01")["questions"]]
    assert "answer" not in exams.get_exam("de-01")["questions"][0]     # không lộ đáp án


def test_dashboard():
    rows = dashboard.tutors_overview()
    assert rows[0]["name"] == "Minh" and rows[0]["sessions_count"] >= 1


def test_hoc_sinh_khong_mo_duoc_phien_gia_su():
    with pytest.raises(ServiceError):
        tutoring.start_session(4, "ham_so")
