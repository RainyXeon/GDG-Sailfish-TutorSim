# Hợp đồng API – TutorSim (v1.3)

- Mọi địa chỉ bắt đầu bằng `/api`, dữ liệu gửi/nhận là JSON. Chạy local: `http://localhost:8000`, thử API: `/docs`.
- Lỗi trả về `{"detail": "lời giải thích"}` với mã 400 (dữ liệu sai), 404 (không có), 409 (phiên đã kết thúc), 503 (Gemini lỗi).
- Muốn đổi hợp đồng: mở Pull Request sửa file này + báo cả nhóm.
- MVP chưa có đăng nhập: chọn tên từ danh sách.

Thay đổi so với v1.2: `POST /api/sessions` nhận thêm `misconception_id`, `persona` (bỏ trống = Coach Agent chọn); báo cáo có thêm `next_chuyen_de`, `next_misconception_id`, `next_persona`; thêm `/api/health`, `/api/misconceptions`, `/api/personas` và `/api/sessions/{id}/debug` (chỉ khi `DEBUG=1`).

## Phân hệ 1: gia sư

| # | Endpoint | Gửi lên | Trả về |
|---|---|---|---|
| 1 | `GET /api/tutors` | | `[{id, name}]` |
| 2 | `GET /api/tutors/{id}/sessions` | | `[{session_id, topic, total, created_at}]` các buổi đã chấm, mới nhất trước |
| 3 | `POST /api/sessions` | `{tutor_id, chuyen_de: "ham_so"\|"oxyz", misconception_id?, persona?}` | `{session_id, student_name, topic, problem, student_solution, geogebra_commands[]}` |
| 4 | `POST /api/sessions/{id}/messages` | `{content}` | `{student_reply, math_warnings[], status: "in_progress"\|"student_understood"}` |
| 5 | `POST /api/sessions/{id}/finish` | `{}` | `{report_id}` (gọi lại nhiều lần vẫn trả cùng báo cáo) |
| 6 | `GET /api/reports/{id}` | | xem dưới |
| 7 | `GET /api/dashboard` | | `[{tutor_id, name, sessions_count, avg_total\|null, last_session\|null}]` |

Báo cáo (mục 6):
```json
{
  "report_id": 13,
  "scores": { "chinh_xac": 4, "chan_doan": 4, "ro_rang": 3, "goi_mo": 3, "thai_do": 4 },
  "total": 3.6,
  "evidence": [ { "criterion": "goi_mo", "quote": "Em thử xét dấu y' hai bên x = 0 xem?", "comment": "Câu hỏi dẫn dắt tốt" } ],
  "feedback": "Bạn chẩn đoán đúng lỗi...",
  "next_recommendation": "Đơn điệu, lỗi HS-03. Giao học sinh thụ động vì tiêu chí yếu nhất là 'Kỹ năng gợi mở'...",
  "next_chuyen_de": "ham_so", "next_misconception_id": "HS-03", "next_persona": "thu_dong"
}
```
- Điểm mỗi tiêu chí 1–4. `total` = trung bình có trọng số (20/25/20/20/15%), do code tính.
- Trạng thái hiểu của Nam và tính cách KHÔNG gửi xuống web (để gia sư không "nhìn đáp án").
- `geogebra_commands`: lệnh GeoGebra (ví dụ `f(x) = x^3 - 3`, `A = (1, 2, 3)`), có thể rỗng.

Phụ trợ: `GET /api/misconceptions?chuyen_de=ham_so` → `[{id, chuyen_de, dang_bai, ten_loi, trang_thai}]`; `GET /api/personas` → `[{id, ten, mo_ta}]`; `GET /api/health` → `{ok, fake_llm, debug, has_gemini_key}`.

**Chỉ khi phát triển** (`DEBUG=1`, dùng cho `cli/chat.py`): `GET /api/sessions/{id}/debug` → lỗi sai, tính cách, các điều kiện, trạng thái, lựa chọn của Coach (kèm tool đã gọi), và từng lượt (điều kiện thỏa, giải hộ, lý do, phát biểu toán, cảnh báo SymPy, độ trễ). Tắt khi deploy.

## Phân hệ 2: học sinh

| # | Endpoint | Gửi lên | Trả về |
|---|---|---|---|
| 8 | `GET /api/students` | | `[{id, name}]` |
| 9 | `GET /api/exams` | | `[{id, title, chuyen_de, num_questions, time_limit_min}]` |
| 10 | `GET /api/exams/{id}` | | `{id, title, time_limit_min, questions: [{id, content, options: {A,B,C,D}}]}` (không có đáp án) |
| 11 | `POST /api/attempts` | `{student_id, exam_id, answers: {"Q01": "B", "Q02": null}, time_spent_sec}` | `{attempt_id, exam_title, correct, total, score10, time_spent_sec, results: [{question_id, chosen, correct_answer, is_correct, misconception_id, misconception_name, explanation}]}` |
| 12 | `GET /api/students/{id}/summary` | | `{attempts[], top_misconceptions: [{id, name, count}], prediction: {low, mid, high}\|null, note}` |
| 13 | `GET /api/insights/misconceptions` | | `[{id, name, count}]` lỗi học sinh cả trung tâm hay mắc (Coach dùng để giao bài cho gia sư) |

Dự đoán (code thường, không LLM): trung bình có trọng số 3 bài gần nhất (cũ → mới: 1, 2, 3), khoảng = độ lệch chuẩn (tối thiểu 0,5); cần ≥ 2 bài.
