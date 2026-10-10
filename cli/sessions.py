"""
XEM LẠI CÁC PHIÊN ĐÃ CHẠY (của tài khoản đang đăng nhập)
    python sessions.py        # danh sách phiên
    python sessions.py 12     # xem lại toàn bộ hội thoại + điểm của phiên #12
"""
import json
import sys

import api

client = api.Client()

if len(sys.argv) < 2:
    for s in client.sessions():
        print(f"#{s['id']:<4} {s['created_at'][:16]}  {s['misconception_id']:<20} {s['persona_key']:<15} "
              f"{s['intent']:<4} {s['state']:<13} {s['status']}")
    sys.exit()

d = client.session(int(sys.argv[1]))
print(f"PHIÊN #{d['id']} | {d['misconception_id']} | {d['persona_key']} | ý định: {d['intent']} | {d['status']}")
print(f"ĐỀ: {d['bai_toan']}\n{d['student_name']}: (nộp bài) {d['loi_giai_sai']}\n")
for t in d["turns"]:
    print(f"Gia sư: {t['tutor_message']}\n{d['student_name']}: {t['student_reply']}")
    print(f"   [trạng thái: {t['state_after']} | lượt này thỏa: {t['satisfied_this_turn']}"
          f"{' | GIẢI HỘ' if t['gives_away_answer'] else ''} | lý do: {t['reason']}]\n")
print(f"Trạng thái cuối: {d['state']} | thỏa: {d['satisfied']}")
if d["evaluation"]:
    print(json.dumps(d["evaluation"], ensure_ascii=False, indent=2))
