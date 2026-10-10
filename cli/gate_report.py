"""
TỔNG HỢP CÁC PHIÊN -> KIỂM TRA "CỔNG" CUỐI BƯỚC 3 (qua REST API)
    python gate_report.py
Server tính số liệu từ TẤT CẢ phiên đã chấm điểm trong database (của mọi người thử nghiệm).
"""
import api

g = api.Client().gate()

if g["good_sessions"] < 10 or g["bad_sessions"] < 10:
    print("Cần có cả phiên giảng tốt và phiên giảng kém (mỗi loại ít nhất 10) đã chấm điểm.")
print(f"Tổng số phiên: {g['total_sessions']}  (giảng tốt: {g['good_sessions']}, giảng kém: {g['bad_sessions']})\n")
print(f"Giảng KÉM mà học sinh vẫn 'hiểu':  {g['bad_still_understood_rate']:.0%}   (cần <= 20%)  "
      f"{'ĐẠT' if g['bad_gate_pass'] else 'CHƯA ĐẠT'}")
print(f"Giảng TỐT và học sinh hiểu được:   {g['good_understood_rate']:.0%}   (cần >= 80%)  "
      f"{'ĐẠT' if g['good_gate_pass'] else 'CHƯA ĐẠT'}")
if g["avg_total_good"] is not None and g["avg_total_bad"] is not None:
    print(f"\nĐiểm TB phiên giảng tốt: {g['avg_total_good']:.2f} | giảng kém: {g['avg_total_bad']:.2f}  (phải chênh rõ)")
print("\nLưu ý: 'nói chuyện tự nhiên' và 'chấm hợp lý' do cả nhóm đọc log và đánh giá bằng mắt.")
