"""
TỔNG HỢP LOG -> KIỂM TRA "CỔNG" CUỐI BƯỚC 3  (người phụ trách: Tech 7)
    python gate_report.py
"""
import json
from pathlib import Path

logs = [json.loads(p.read_text(encoding="utf-8")) for p in Path("logs").glob("*.json")]
good = [l for l in logs if l["intent"] == "tot"]
bad = [l for l in logs if l["intent"] == "kem"]


def rate(items):
    return sum(l["reached_da_hieu"] for l in items) / len(items) if items else 0


if not good or not bad:
    print("Cần có cả phiên giảng tốt và phiên giảng kém (mỗi loại ít nhất 10) trong thư mục logs/.")
print(f"Tổng số phiên: {len(logs)}  (giảng tốt: {len(good)}, giảng kém: {len(bad)})\n")
r_bad, r_good = rate(bad), rate(good)
print(f"Giảng KÉM mà học sinh vẫn 'hiểu':  {r_bad:.0%}   (cần <= 20%)  {'ĐẠT' if r_bad <= 0.2 else 'CHƯA ĐẠT'}")
print(f"Giảng TỐT và học sinh hiểu được:   {r_good:.0%}   (cần >= 80%)  {'ĐẠT' if r_good >= 0.8 else 'CHƯA ĐẠT'}")
if good and bad:
    avg = lambda xs: sum(l["total"] for l in xs) / len(xs)
    print(f"\nĐiểm TB phiên giảng tốt: {avg(good):.2f} | giảng kém: {avg(bad):.2f}  (phải chênh rõ)")
print("\nLưu ý: 'nói chuyện tự nhiên' và 'chấm hợp lý' do cả nhóm đọc log và đánh giá bằng mắt.")
