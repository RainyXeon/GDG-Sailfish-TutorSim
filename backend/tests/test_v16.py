"""v1.6: endpoint mới cho frontend + sửa lỗi 502/503/504 khi kết thúc buổi sớm. Chạy không cần API key."""
import threading
import time

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from agent import llm  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.tutoring import service as tutoring_service  # noqa: E402  (test được phép nhìn ruột module)
from settings import settings  # noqa: E402

c = TestClient(app)


def auth(username, password="demo1234"):
    r = c.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def new_session(h, cd="ham_so"):
    return c.post("/api/sessions", json={"chuyen_de": cd}, headers=h).json()["session_id"]


# ---------------- Phân hệ 1: endpoint mới ----------------
def test_chi_tiet_buoi_va_hoi_thoai():
    h = auth("minh")
    sid = new_session(h)
    c.post(f"/api/sessions/{sid}/messages", json={"content": "Em xét dấu y' xem"}, headers=h)
    d = c.get(f"/api/sessions/{sid}", headers=h).json()
    assert d["status"] == "in_progress" and d["report_id"] is None
    assert [m["role"] for m in d["messages"]] == ["tutor", "student"]
    assert "misconception_id" not in d and "state" not in d and "conditions" not in d   # không lộ "đáp án"
    assert d["persona"] and d["persona_name"]                                            # tính cách được hiển thị (v1.7)
    c.post(f"/api/sessions/{sid}/finish", headers=h)
    d = c.get(f"/api/sessions/{sid}", headers=h).json()
    assert d["status"] == "finished" and d["report_id"] == sid
    assert c.get(f"/api/sessions/{sid}", headers=auth("lan")).status_code == 403
    assert c.get(f"/api/sessions/{sid}", headers=auth("quanly", "quanly-mat-khau")).status_code == 200


def test_huy_buoi():
    h = auth("minh")
    sid = new_session(h)
    assert c.post(f"/api/sessions/{sid}/abandon", headers=h).json() == {"session_id": sid, "status": "abandoned"}
    assert c.post(f"/api/sessions/{sid}/abandon", headers=h).status_code == 200            # gọi lại vẫn được
    assert c.post(f"/api/sessions/{sid}/messages", json={"content": "x"}, headers=h).status_code == 409
    assert c.post(f"/api/sessions/{sid}/finish", headers=h).status_code == 409
    me = c.get("/api/auth/me", headers=h).json()["id"]
    done = c.get(f"/api/tutors/{me}/sessions", headers=h).json()
    assert all(s["total"] is not None for s in done)                                        # mặc định như cũ
    allx = c.get(f"/api/tutors/{me}/sessions?include_unfinished=true", headers=h).json()
    assert any(s["session_id"] == sid and s["status"] == "abandoned" and s["total"] is None for s in allx)


def test_next_chuyen_de_theo_loi_coach_goi_y():
    h = auth("tuan")
    sid = new_session(h, "oxyz")
    c.post(f"/api/sessions/{sid}/messages", json={"content": "Em kiểm tra lại công thức"}, headers=h)
    c.post(f"/api/sessions/{sid}/finish", headers=h)
    r = c.get(f"/api/reports/{sid}", headers=h).json()
    assert r["next_misconception_id"].startswith("OX") and r["next_chuyen_de"] == "oxyz"


# ---------------- Phân hệ 2: endpoint mới ----------------
def test_xem_lai_bai_thi_va_ve_lam_bai():
    hs = auth("ha")
    exam = c.get("/api/exams", headers=hs).json()[0]
    qids = [q["id"] for q in c.get(f"/api/exams/{exam['id']}", headers=hs).json()["questions"]]
    t = c.post(f"/api/exams/{exam['id']}/start", headers=hs).json()
    assert t["time_limit_sec"] == exam["time_limit_min"] * 60
    r = c.post("/api/attempts", json={"exam_id": exam["id"], "answers": {qids[0]: "A"}, "time_spent_sec": 99999,
                                       "attempt_token": t["attempt_token"]}, headers=hs).json()
    assert r["time_spent_sec"] < 60 and r["late"] is False       # có vé -> server tự đo, bỏ qua số trình duyệt gửi
    d = c.get(f"/api/attempts/{r['attempt_id']}", headers=hs).json()
    assert d["exam_id"] == exam["id"] and len(d["results"]) == len(qids) and d["created_at"]
    assert c.get(f"/api/attempts/{r['attempt_id']}", headers=auth("khoa")).status_code == 403
    assert c.get(f"/api/attempts/{r['attempt_id']}", headers=auth("quanly", "quanly-mat-khau")).status_code == 200
    assert c.get(f"/api/attempts/{r['attempt_id']}", headers=auth("minh")).status_code == 403


def test_nop_bai_kiem_tra_du_lieu():
    hs = auth("ha")
    exam = c.get("/api/exams", headers=hs).json()[0]
    late = c.post("/api/attempts", json={"exam_id": exam["id"], "answers": {}, "time_spent_sec": 10 ** 6}, headers=hs).json()
    assert late["late"] is True
    # dữ liệu lạ không làm mất bài: mã câu lạ bị bỏ qua, thời gian âm tính là 0
    r = c.post("/api/attempts", json={"exam_id": exam["id"], "answers": {"KHONG_CO": "A"}, "time_spent_sec": -5}, headers=hs)
    assert r.status_code == 200 and r.json()["time_spent_sec"] == 0
    khoa = auth("khoa")
    other = c.post("/api/exams/" + exam["id"] + "/start", headers=hs).json()["attempt_token"]
    assert c.post("/api/attempts", json={"exam_id": exam["id"], "answers": {}, "attempt_token": other},
                  headers=khoa).status_code == 400                # vé của Hà không dùng được cho Khoa


# ---------------- Lỗi khi kết thúc buổi sớm ----------------
def test_ket_thuc_khi_nam_chua_tra_loi_xong(monkeypatch):
    """Gia sư gửi tin rồi bấm Kết thúc ngay khi Nam còn đang trả lời. Trước: chạy chồng nhau
    (hoặc 400 'chưa có tin nhắn'). Giờ: Kết thúc chờ lượt đó xong rồi chấm luôn cả lượt đó."""
    h = auth("minh")
    sid = new_session(h)
    real = tutoring_service.student_reply

    def slow_reply(*a, **k):
        time.sleep(0.8)
        return real(*a, **k)
    monkeypatch.setattr(tutoring_service, "student_reply", slow_reply)
    res = {}
    t = threading.Thread(target=lambda: res.setdefault("msg", c.post(f"/api/sessions/{sid}/messages",
                                                                     json={"content": "Em xét dấu y'"}, headers=h)))
    t.start()
    time.sleep(0.2)
    fin = c.post(f"/api/sessions/{sid}/finish", headers=h)
    t.join()
    assert res["msg"].status_code == 200
    assert fin.status_code == 200, fin.text
    assert len(c.get(f"/api/sessions/{sid}", headers=h).json()["messages"]) == 2


def test_bam_ket_thuc_hai_lan_cung_luc():
    h = auth("lan")
    sid = new_session(h)
    c.post(f"/api/sessions/{sid}/messages", json={"content": "Em thử lại xem"}, headers=h)
    out = []
    ts = [threading.Thread(target=lambda: out.append(c.post(f"/api/sessions/{sid}/finish", headers=h))) for _ in range(3)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert [r.status_code for r in out] == [200, 200, 200]          # trước: có thể 500 do trùng khóa bảng reports


def test_ket_thuc_khong_cho_coach(monkeypatch):
    """Coach Agent chậm không còn kéo dài request Kết thúc (nguyên nhân 502/504 qua proxy)."""
    h = auth("minh")
    sid = new_session(h)
    c.post(f"/api/sessions/{sid}/messages", json={"content": "Em xét dấu y'"}, headers=h)
    real = tutoring_service.plan_next_for

    def slow_coach(*a, **k):
        time.sleep(3)
        return real(*a, **k)
    monkeypatch.setattr(tutoring_service, "plan_next_for", slow_coach)
    monkeypatch.setattr(settings, "coach_wait_in_report_sec", 1)
    t0 = time.time()
    assert c.post(f"/api/sessions/{sid}/finish", headers=h).status_code == 200
    assert time.time() - t0 < 1.5
    r = c.get(f"/api/reports/{sid}", headers=h).json()             # Coach chưa xong -> luật dự phòng, vẫn có gợi ý
    assert r["next_misconception_id"] and r["next_recommendation"]
    time.sleep(2.5)                                                 # Coach xong sau đó cũng không đổi gợi ý đã hiện
    assert c.get(f"/api/reports/{sid}", headers=h).json()["next_misconception_id"] == r["next_misconception_id"]


def test_gemini_loi_tra_503_kem_retry_after(monkeypatch):
    h = auth("tuan")
    sid = new_session(h)

    def boom(*a, **k):
        raise llm.LLMError("Gemini đang hết hạn mức gọi (429).", kind="quota", retry_after=37)
    monkeypatch.setattr(tutoring_service, "classify", boom)
    r = c.post(f"/api/sessions/{sid}/messages", json={"content": "x"}, headers=h)
    assert r.status_code == 503 and r.headers["retry-after"] == "37"


# ---------------- Lớp gọi Gemini ----------------
class FakeAPIError(Exception):
    def __init__(self, code, text):
        super().__init__(f"{code} {text}")
        self.code = code


class FakeClient:
    def __init__(self, errors, delay=0):
        self.errors, self.calls, self.delay = list(errors), 0, delay
        self.models = self

    def generate_content(self, **_):
        self.calls += 1
        time.sleep(self.delay)
        if self.errors:
            raise self.errors.pop(0)

        class R:
            text = "ok"
            parsed = None
        return R()


def _cfg():
    from google.genai import types
    return types.GenerateContentConfig()


def test_llm_429_theo_phut_cho_roi_thu_lai(monkeypatch):
    pytest.importorskip("google.genai")
    fc = FakeClient([FakeAPIError(429, "RESOURCE_EXHAUSTED {'retryDelay': '1s'}")])
    monkeypatch.setattr(llm, "_client_", lambda: fc)
    t0 = time.time()
    assert llm._call("m", "p", _cfg(), retries=3, budget_sec=30).text == "ok"
    assert fc.calls == 2 and time.time() - t0 >= 1


def test_llm_het_han_muc_ngay_khong_thu_lai(monkeypatch):
    pytest.importorskip("google.genai")
    fc = FakeClient([FakeAPIError(429, "RESOURCE_EXHAUSTED GenerateRequestsPerDayPerProjectPerModel")] * 3)
    monkeypatch.setattr(llm, "_client_", lambda: fc)
    with pytest.raises(llm.LLMError) as e:
        llm._call("m", "p", _cfg(), retries=3, budget_sec=30)
    assert fc.calls == 1 and e.value.kind == "quota"


def test_llm_khong_vuot_ngan_sach_thoi_gian(monkeypatch):
    pytest.importorskip("google.genai")
    fc = FakeClient([FakeAPIError(503, "UNAVAILABLE overloaded")] * 10, delay=1)
    monkeypatch.setattr(llm, "_client_", lambda: fc)
    t0 = time.time()
    with pytest.raises(llm.LLMError) as e:
        llm._call("m", "p", _cfg(), retries=10, budget_sec=8)
    assert time.time() - t0 < 8 and e.value.kind == "overloaded"


def test_llm_json_hong_thanh_loi_503_khong_phai_500(monkeypatch):
    pytest.importorskip("google.genai")
    from agent.evaluator import EvalResult

    class Bad:
        text, parsed = "", None
    monkeypatch.setattr(llm, "_call", lambda *a, **k: Bad())
    monkeypatch.setattr(settings, "fake_llm", False)
    with pytest.raises(llm.LLMError) as e:
        llm.ask_json("p", EvalResult, budget_sec=20)
    assert e.value.kind == "bad_output"
