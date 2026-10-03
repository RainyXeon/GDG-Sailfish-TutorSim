"""
CHẠY THỬ MỘT PHIÊN LUYỆN TẬP TRONG TERMINAL
    python run_chat.py
Gõ 'q' để kết thúc phiên và chấm điểm. Mỗi phiên lưu 1 file vào thư mục logs/.
"""
import json
from datetime import datetime
from pathlib import Path

from data import MISCONCEPTIONS, PERSONAS
from state_machine import KnowledgeState, DA_HIEU
from classifier import classify
from simulator import student_reply
from evaluator import evaluate

STUDENT = "Nam"


def choose(title, options):
    print(f"\n{title}")
    for i, o in enumerate(options):
        print(f"  {i}. {o}")
    while True:
        ans = input("Chọn số: ").strip() or "0"
        if ans.isdigit() and int(ans) < len(options):
            return options[int(ans)]
        print("  Nhập lại số thứ tự trong danh sách.")


def main():
    tester = input("Tên người thử nghiệm: ").strip() or "an_danh"
    mis = choose("Chọn lỗi sai:", [m["id"] for m in MISCONCEPTIONS])
    mis = next(m for m in MISCONCEPTIONS if m["id"] == mis)
    persona_key = choose("Chọn tính cách học sinh:", list(PERSONAS))
    intent = choose("Lần này bạn định giảng TỐT hay cố tình giảng KÉM/SAI?", ["tot", "kem"])

    state = KnowledgeState(len(mis["dieu_kien_hieu_ra"]))
    turns = []
    history = f"{STUDENT}: (nộp bài) {mis['loi_giai_sai']}"

    print("\n" + "=" * 60)
    print(f"ĐỀ: {mis['bai_toan']}")
    print(f"BÀI LÀM CỦA {STUDENT.upper()}: {mis['loi_giai_sai']}")
    print("=" * 60 + "\n(gõ q để kết thúc)\n")

    while True:
        tutor = input("Gia sư: ").strip()
        if tutor.lower() == "q":
            break
        if not tutor:
            continue
        c = classify(tutor, mis, history)
        new_state = state.update(c.satisfied)
        history += f"\nGia sư: {tutor}"
        reply = student_reply(mis, PERSONAS[persona_key], new_state, history, STUDENT)
        history += f"\n{STUDENT}: {reply}"
        print(f"{STUDENT}: {reply}")
        # Dòng dưới chỉ hiện trong prototype để người thử nghiệm theo dõi. Sản phẩm thật sẽ ẩn.
        print(f"   [trạng thái: {new_state} | thỏa: {sorted(state.satisfied)} | lý do: {c.reason}]\n")
        turns.append({"tutor": tutor, "student": reply, "state": new_state,
                      "satisfied_this_turn": c.satisfied, "gives_away": c.gives_away_answer, "reason": c.reason})

    print("\nĐang chấm điểm...")
    result, total = evaluate(history, mis)
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    print(f"ĐIỂM TỔNG (code tính): {total}")

    log = {"tester": tester, "time": datetime.now().isoformat(timespec="seconds"),
           "misconception": mis["id"], "persona": persona_key, "intent": intent,
           "final_state": state.state, "reached_da_hieu": state.state == DA_HIEU,
           "turns": turns, "evaluation": result.model_dump(), "total": total}
    Path("logs").mkdir(exist_ok=True)
    path = Path("logs") / f"{datetime.now():%Y%m%d-%H%M%S}-{tester}.json"
    path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã lưu: {path}")


if __name__ == "__main__":
    main()
