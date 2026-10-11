"""
CLI THỬ NGHIỆM HỌC SINH ẢO - là "khách" gọi REST API, KHÔNG chứa logic agent.
1) Chạy backend trước:  cd backend && uvicorn app.main:app --reload
2) Chạy:               python cli/chat.py          (gõ q để kết thúc và chấm điểm)
Đăng nhập bằng tài khoản gia sư (mặc định tài khoản thử "minh" / mật khẩu trong DEMO_PASSWORD).
Đặt sẵn để khỏi gõ lại:  CLI_USERNAME=minh  CLI_PASSWORD=demo1234
Mỗi phiên lưu 1 file vào cli/logs/ để gate_report.py tổng hợp.
Chỉ dùng thư viện có sẵn của Python, không cần cài thêm.
"""
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

API = os.getenv("API_URL", "http://localhost:8000")
LOG_DIR = Path(__file__).parent / "logs"
TOKEN = None


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=int(os.getenv("CLI_TIMEOUT_SEC", "180"))) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:                 # server trả lỗi (401, 403, 503...)
        detail = e.read().decode()
        try:
            detail = json.loads(detail).get("detail", detail)
        except ValueError:
            pass
        raise SystemExit(f"\nLỗi {e.code} khi gọi {path}: {detail}")
    except (TimeoutError, urllib.error.URLError, OSError) as e:
        reason = getattr(e, "reason", e)
        if isinstance(e, TimeoutError) or isinstance(reason, TimeoutError) or "timed out" in str(reason):
            raise SystemExit("\nServer trả lời quá chậm (Gemini đang chậm hoặc quá tải). Xem cửa sổ backend có báo lỗi không, "
                             "đợi 1 phút rồi chạy lại. Mẹo: chọn sẵn lỗi sai và tính cách để bỏ qua bước Coach.")
        raise SystemExit(f"\nKhông kết nối được {API}. Đã chạy backend chưa? (cd backend && uvicorn app.main:app --reload)")


def choose(title, options, allow_skip=False):
    print(f"\n{title}")
    if allow_skip:
        print("  Enter. Để Coach Agent tự chọn")
    for i, (_, label) in enumerate(options):
        print(f"  {i}. {label}")
    while True:
        a = input("Chọn số: ").strip()
        if allow_skip and a == "":
            return None
        if a.isdigit() and int(a) < len(options):
            return options[int(a)][0]
        print("  Nhập lại số thứ tự trong danh sách.")


def main():
    health = call("GET", "/api/health")
    if not health["debug"]:
        print("Lưu ý: backend đang tắt DEBUG nên không xem được trạng thái ẩn của Nam.")
    print(f"Backend: {'GIẢ (FAKE_LLM=1)' if health['fake_llm'] else 'Gemini thật'}")
    global TOKEN
    username = os.getenv("CLI_USERNAME") or input("Tên đăng nhập gia sư [minh]: ").strip() or "minh"
    password = os.getenv("CLI_PASSWORD") or getpass.getpass("Mật khẩu: ")
    auth = call("POST", "/api/auth/login", {"username": username, "password": password})
    TOKEN = auth["token"]
    if auth["user"]["role"] != "tutor":
        raise SystemExit("CLI dùng để thử học sinh ảo, hãy đăng nhập bằng tài khoản gia sư.")
    print(f"Đã đăng nhập: {auth['user']['name']} ({auth['user']['username']})")
    tester = input("Tên người thử nghiệm (ghi vào log): ").strip() or username
    cd = choose("Chuyên đề:", [("ham_so", "Hàm số"), ("oxyz", "Hình học Oxyz")])
    mis = call("GET", f"/api/misconceptions?chuyen_de={cd}")
    mid = choose("Lỗi sai của Nam:", [(m["id"], f"{m['id']}  {m['ten_loi']}") for m in mis], allow_skip=True)
    personas = call("GET", "/api/personas")
    persona = choose("Tính cách của Nam:", [(p["id"], p["ten"]) for p in personas], allow_skip=True)
    intent = choose("Lần này bạn định giảng TỐT hay cố tình giảng KÉM/SAI?", [("tot", "tốt"), ("kem", "kém / sai")])

    if not mid or not persona:
        print("\nCoach Agent đang chọn bài (có thể mất 10–25 giây)...")
    s = call("POST", "/api/sessions", {"chuyen_de": cd, "misconception_id": mid, "persona": persona})
    sid = s["session_id"]
    dbg = call("GET", f"/api/sessions/{sid}/debug") if health["debug"] else {}
    print("\n" + "=" * 64)
    print(f"ĐỀ: {s['problem']}")
    print(f"BÀI LÀM CỦA {s['student_name'].upper()}: {s['student_solution']}")
    if dbg:
        print(f"[ẩn] lỗi {dbg['misconception_id']} | tính cách {dbg['persona']}"
              + (f" | Coach ({dbg['coach']['source']}): {dbg['coach']['reason']}" if dbg.get("coach") else " | bạn tự chọn cả hai"))
        if (dbg.get("coach") or {}).get("user_override"):
            print(f"[ẩn] {dbg['coach']['user_override']}")
        for i, c in enumerate(dbg["conditions"]):
            print(f"[ẩn] điều kiện {i}: {c}")
    print("=" * 64 + "\n(gõ q để kết thúc)\n")

    while True:
        text = input("Gia sư: ").strip()
        if text.lower() == "q":
            break
        if not text:
            continue
        print("   (Nam đang nghĩ...)")
        r = call("POST", f"/api/sessions/{sid}/messages", {"content": text})
        print(f"{s['student_name']}: {r['student_reply']}")
        for w in r["math_warnings"]:
            print(f"   ⚠ SymPy: {w}")
        if health["debug"]:
            t = [x for x in call("GET", f"/api/sessions/{sid}/debug")["turns"] if x["role"] == "tutor"][-1]
            print(f"   [{t['state_after']} | thỏa lượt này {t['satisfied_this_turn']} | tổng {t['satisfied_total']}"
                  f" | thuyết phục {t['convincing_turns']}/{t['turns_needed']}{' | GIẢI HỘ' if t['gives_away'] else ''}"
                  f" | {t['latency_ms']} ms | {t['reason']}]\n")
        if r["status"] == "student_understood":
            print("   (Nam đã hiểu ra. Gõ q để kết thúc và xem nhận xét.)\n")

    print("\nĐang chấm điểm và chọn buổi tiếp theo (có thể mất 20–40 giây)...")
    call("POST", f"/api/sessions/{sid}/finish")
    rep = call("GET", f"/api/reports/{sid}")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    final = call("GET", f"/api/sessions/{sid}/debug") if health["debug"] else {"state": {}}
    LOG_DIR.mkdir(exist_ok=True)
    path = LOG_DIR / f"{datetime.now():%Y%m%d-%H%M%S}-{tester}.json"
    path.write_text(json.dumps({"tester": tester, "time": datetime.now().isoformat(timespec="seconds"), "intent": intent,
                                "fake_llm": health["fake_llm"], "reached_da_hieu": final["state"].get("state") == "da_hieu",
                                "report": rep, "debug": final}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã lưu: {path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nĐã thoát.")
