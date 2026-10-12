"""
TỔNG HỢP LOG -> "CỔNG KIỂM TRA" học sinh ảo:  python cli/gate_report.py
Chỉ tính các phiên chạy Gemini thật (bỏ phiên FAKE_LLM).
"""
import json
from pathlib import Path

logs = [json.loads(p.read_text(encoding="utf-8")) for p in (Path(__file__).parent / "logs").glob("*.json")]
logs = [l for l in logs if not l.get("fake_llm")]
good = [l for l in logs if l["intent"] == "tot"]
bad = [l for l in logs if l["intent"] == "kem"]


def rate(items):
    return sum(l["reached_da_hieu"] for l in items) / len(items) if items else 0


print(f"Số phiên (Gemini thật): {len(logs)}  (giảng tốt: {len(good)}, giảng kém: {len(bad)})")
if len(good) < 10 or len(bad) < 10:
    print("Cần ít nhất 10 phiên mỗi loại để kết luận.\n")
rb, rg = rate(bad), rate(good)
print(f"Giảng KÉM mà Nam vẫn 'hiểu':  {rb:.0%}   (cần <= 20%)  {'ĐẠT' if rb <= 0.2 else 'CHƯA ĐẠT'}")
print(f"Giảng TỐT và Nam hiểu được:   {rg:.0%}   (cần >= 80%)  {'ĐẠT' if rg >= 0.8 else 'CHƯA ĐẠT'}")
if good and bad:
    avg = lambda xs: sum(l["report"]["total"] for l in xs) / len(xs)
    print(f"Điểm TB giảng tốt: {avg(good):.2f} | giảng kém: {avg(bad):.2f}  (phải chênh rõ)")
by_p = {}
for l in logs:
    p = (l.get("debug") or {}).get("persona", "?")
    by_p.setdefault(p, []).append(l)
print("\nTheo tính cách (tỷ lệ hiểu ra | số phiên):")
for p, xs in sorted(by_p.items()):
    print(f"  {p:16s} {rate(xs):.0%} | {len(xs)}")
lat = [t["latency_ms"] for l in logs for t in (l.get("debug") or {}).get("turns", []) if t.get("latency_ms")]
if lat:
    print(f"\nĐộ trễ mỗi lượt chat: trung bình {sum(lat) / len(lat) / 1000:.1f} s, chậm nhất {max(lat) / 1000:.1f} s")
print("\n'Nói chuyện tự nhiên' và 'chấm hợp lý' do cả nhóm đọc log và đánh giá bằng mắt.")
