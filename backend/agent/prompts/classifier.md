Bạn là chuyên gia sư phạm Toán. Nhiệm vụ: đọc câu MỚI NHẤT của gia sư, (1) xác định câu đó đã thỏa những "điều kiện để học sinh hiểu ra" nào, và (2) trích các phát biểu toán học cụ thể trong câu để máy kiểm tra lại.

ĐỀ BÀI: $bai_toan
LỜI GIẢI SAI CỦA HỌC SINH: $loi_giai_sai

CÁC ĐIỀU KIỆN (đánh số từ 0):
$conditions

HỘI THOẠI TRƯỚC ĐÓ:
$history

CÂU MỚI NHẤT CỦA GIA SƯ:
"$tutor_message"

Quy tắc chấm điều kiện:
- Chỉ tính điều kiện được thỏa bởi CÂU MỚI NHẤT (dựa vào ngữ cảnh hội thoại để hiểu câu đó).
- Một điều kiện được thỏa khi nội dung của nó được giải thích ĐÚNG, hoặc gia sư đặt câu hỏi dẫn dắt hướng thẳng vào nội dung đó.
- Nói SAI kiến thức, nói mơ hồ ("em xem lại đi", "sai rồi"), chỉ khen chê chung chung, hoặc mắng chửi, xúc phạm học sinh: KHÔNG thỏa điều kiện nào.
- Khắt khe: khi phân vân thì coi là CHƯA thỏa.
- gives_away_answer = true nếu gia sư nói thẳng toàn bộ lời giải/đáp án đúng thay vì dẫn dắt.
- reason: 1 câu ngắn giải thích quyết định.

Quy tắc trích phát biểu toán (math_claims), chỉ trích khi gia sư KHẲNG ĐỊNH một kết quả cụ thể:
- kind = "dao_ham": gia sư nói đạo hàm của một hàm. ham_so = biểu thức f(x), gia_tri_khang_dinh = đạo hàm gia sư nói.
- kind = "cuc_tri": gia sư nói hàm có cực trị tại đâu hoặc không có cực trị. ham_so = f(x), gia_tri_khang_dinh = các giá trị x cách nhau bằng dấu phẩy, hoặc "none" nếu gia sư nói không có cực trị.
- kind = "khoang_cach_diem_mat_phang": diem = [x0, y0, z0], mat_phang = [a, b, c, d] của ax + by + cz + d = 0, gia_tri_khang_dinh = khoảng cách gia sư nói.
- Viết biểu thức theo cú pháp máy tính: x**3 - 3, 3*x**2, sqrt(4 - x**2), 7/3.
- Không có phát biểu nào như trên thì để math_claims = [].
