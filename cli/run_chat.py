"""
CHẠY THỬ MỘT PHIÊN LUYỆN TẬP TRONG TERMINAL (qua REST API)
    python run_chat.py              # cần server rest_api đang chạy
    python run_chat.py --relogin    # đăng nhập bằng tài khoản khác
Gõ 'q' để kết thúc phiên và chấm điểm. Phiên được lưu trong database của server,
đồng thời lưu 1 bản JSON vào thư mục logs/ (cùng định dạng prototype) để đọc lại bằng mắt.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import api

STUDENT = "Nam"
LOG_DIR = Path(__file__).parent / "logs"


def choose(title, options, labels=None):
    print(f"\n{title}")
    for i, o in enumerate(labels or options):
        print(f"  {i}. {o}")
    while True:
        ans = input("Chọn số: ").strip() or "0"
        if ans.isdigit() and int(ans) < len(options):
            return options[int(ans)]
        print("  Nhập lại số thứ tự trong danh sách.")


def main():
    if "--relogin" in sys.argv:
        api.logout()
    client = api.Client()
    tester = client.me()["username"]
    print(f"Người thử nghiệm: {tester}  (server: {api.BASE_URL})")

    mis_list = client.misconceptions()
    mis_id = choose("Chọn lỗi sai:", [m["id"] for m in mis_list],
                    [f"{m['id']}  ({m['chuyen_de']}: {m['ten_loi']})" for m in mis_list])
    personas = client.personas()
    persona_key = choose("Chọn tính cách học sinh:", [p["key"] for p in personas],
                         [f"{p['key']}  - {p['description']}" for p in personas])
    intent = choose("Lần này bạn định giảng TỐT hay cố tình giảng KÉM/SAI?", ["tot", "kem"])

    session = client.start_session(mis_id, persona_key, intent, STUDENT)
    sid = session["id"]

    print("\n" + "=" * 60)
    print(f"PHIÊN #{sid}")
    print(f"ĐỀ: {session['bai_toan']}")
    print(f"BÀI LÀM CỦA {STUDENT.upper()}: {session['loi_giai_sai']}")
    print("=" * 60 + "\n(gõ q để kết thúc)\n")

    try:
        while True:
            tutor = input("Gia sư: ").strip()
            if tutor.lower() == "q":
                break
            if not tutor:
                continue
            try:
                t = client.add_turn(sid, tutor)
            except api.ApiError as e:
                print(f"   [lỗi server: {e}]\n")
                continue
            satisfied = client.session(sid)["satisfied"]
            print(f"{STUDENT}: {t['student_reply']}")
            # Dòng dưới chỉ để người thử nghiệm theo dõi. Sản phẩm thật sẽ ẩn.
            print(f"   [trạng thái: {t['state_after']} | thỏa: {satisfied} | lượt này thỏa: {t['satisfied_this_turn']}"
                  f"{' | GIẢI HỘ' if t['gives_away_answer'] else ''} | lý do: {t['reason']}]\n")
    except (KeyboardInterrupt, EOFError):
        print(f"\nĐã dừng. Phiên #{sid} vẫn đang mở trên server (chưa chấm điểm).")
        return

    detail = client.session(sid)
    if not detail["turns"]:
        print("Chưa có lượt nào nên không chấm điểm.")
        return

    print("\nĐang chấm điểm...")
    evaluation = client.finish(sid)
    total = evaluation.pop("total")
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))
    print(f"ĐIỂM TỔNG (code tính): {total}")

    detail = client.session(sid)
    log = {"tester": tester, "time": datetime.now().isoformat(timespec="seconds"), "session_id": sid,
           "misconception": mis_id, "persona": persona_key, "intent": intent,
           "final_state": detail["state"], "reached_da_hieu": detail["state"] == "da_hieu",
           "turns": [{"tutor": x["tutor_message"], "student": x["student_reply"], "state": x["state_after"],
                      "satisfied_this_turn": x["satisfied_this_turn"], "gives_away": x["gives_away_answer"],
                      "reason": x["reason"]} for x in detail["turns"]],
           "evaluation": evaluation, "total": total}
    LOG_DIR.mkdir(exist_ok=True)
    path = LOG_DIR / f"{datetime.now():%Y%m%d-%H%M%S}-{tester}.json"
    path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã lưu: {path}")


if __name__ == "__main__":
    main()
