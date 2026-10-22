# API – TutorSim

Tài liệu về API của TutorSim, có thể chạy backend đọc `localhost:8000/docs`

## Tài khoản

| Endpoint | Ai dùng | Gửi lên | Trả về |
|---|---|---|---|
| `POST /api/auth/register` | Công khai (khi `ALLOW_REGISTER=1`) | `{username, password, name, role: "tutor"\|"student"}` | `{token, user}` |
| `POST /api/auth/login` | Công khai | `{username, password}` | `{token, user}` |
| `GET /api/auth/me` | Đã đăng nhập | | `{id, username, name, role, created_at}` |

- `username`: 3–32 ký tự, chữ thường không dấu, số, `.` `_` (tự chuyển về chữ thường). `password`: ≥ 8 ký tự.
- Tài khoản `manager` không tự đăng ký được; tạo từ `MANAGER_USERNAME`/`MANAGER_PASSWORD` khi khởi động.
- Token hết hạn sau `JWT_EXPIRE_DAYS` ngày (mặc định 7).

## Phân hệ 1: gia sư

| # | Endpoint | Ai dùng | Gửi lên | Trả về |
|---|---|---|---|---|
| 1 | `GET /api/tutors` | quản lý | | `[{id, name}]` |
| 2 | `GET /api/tutors/{id}/sessions` | gia sư đó, quản lý | | `[{session_id, topic, total, created_at}]` các buổi đã chấm, mới nhất trước |
| 3 | `POST /api/sessions` | gia sư | `{chuyen_de: "ham_so"\|"oxyz", misconception_id?, persona?}` | `{session_id, student_name, topic, problem, student_solution, geogebra_commands[]}` |
| 4 | `POST /api/sessions/{id}/messages` | gia sư chủ phiên | `{content}` | `{student_reply, math_warnings[], status: "in_progress"\|"student_understood"}` |
| 5 | `POST /api/sessions/{id}/finish` | gia sư chủ phiên | `{}` | `{report_id}` (gọi lại nhiều lần vẫn trả cùng báo cáo) |
| 6 | `GET /api/reports/{id}` | gia sư chủ phiên, quản lý | | xem dưới |
| 7 | `GET /api/dashboard` | quản lý | | `[{tutor_id, name, sessions_count, avg_total\|null, last_session\|null}]` |
| 7a | `GET /api/sessions/{id}` | gia sư chủ phiên, quản lý | | `{session_id, student_name, topic, chuyen_de, problem, student_solution, geogebra_commands[], status: "in_progress"\|"finished"\|"abandoned", student_understood, created_at, finished_at\|null, report_id\|null, messages: [{role: "tutor"\|"student", content, created_at, math_warnings[]}]}` |
| 7b | `POST /api/sessions/{id}/abandon` | gia sư chủ phiên | `{}` | `{session_id, status: "abandoned"}` (phiên đã chấm → 409) |

- Mục 2 thêm tham số `?include_unfinished=true`: trả cả buổi đang dở / đã hủy với `total: null`. Mỗi dòng có thêm `status`.

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
- Trạng thái hiểu của Nam và lỗi sai KHÔNG gửi xuống web (để gia sư không "nhìn đáp án"). Tính cách được hiển thị từ v1.7.
- `geogebra_commands`: lệnh GeoGebra (ví dụ `f(x) = x^3 - 3`, `A = (1, 2, 3)`), có thể rỗng.

Phụ trợ (đã đăng nhập): `GET /api/misconceptions?chuyen_de=ham_so` → `[{id, chuyen_de, dang_bai, ten_loi, trang_thai}]`; `GET /api/personas` → `[{id, ten, mo_ta}]`; `GET /api/health` (công khai) → `{ok, fake_llm, debug, has_gemini_key, allow_register}` (màn đăng nhập dùng `allow_register` để ẩn/hiện nút Tạo tài khoản).

**Chỉ  dùng khi phát triển** (`DEBUG=1`, gia sư chủ phiên hoặc quản lý, dùng cho `cli/chat.py`): `GET /api/sessions/{id}/debug` → lỗi sai, tính cách, các điều kiện, trạng thái, lựa chọn của Coach (kèm tool đã gọi), và từng lượt (điều kiện thỏa, giải hộ, lý do, phát biểu toán, cảnh báo SymPy, độ trễ). Tắt khi deploy.

## Phân hệ 2: học sinh

| # | Endpoint | Ai dùng | Gửi lên | Trả về |
|---|---|---|---|---|
| 8 | `GET /api/students` | quản lý | | `[{id, name}]` |
| 9 | `GET /api/exams` | đã đăng nhập | | `[{id, title, chuyen_de, num_questions, time_limit_min}]` |
| 10 | `GET /api/exams/{id}` | đã đăng nhập | | `{id, title, time_limit_min, questions: [{id, content, options: {A,B,C,D}}]}` (không có đáp án) |
| 10a | `POST /api/exams/{id}/start` | học sinh | | `{attempt_token, exam_id, time_limit_sec}` (tùy chọn) |
| 11 | `POST /api/attempts` | học sinh | `{exam_id, answers: {"Q01": "B", "Q02": null}, time_spent_sec, attempt_token?}` | `{attempt_id, exam_title, correct, total, score10, time_spent_sec, late, results: [{question_id, chosen, correct_answer, is_correct, misconception_id, misconception_name, explanation}]}` |
| 11a | `GET /api/attempts/{id}` | học sinh đó, quản lý | | như mục 11, thêm `student_id, exam_id, created_at` |
| 12 | `GET /api/students/{id}/summary` | học sinh đó, quản lý | | `{attempts[], top_misconceptions: [{id, name, count}], prediction: {low, mid, high}\|null, note}` |
| 13 | `GET /api/insights/misconceptions` | quản lý | | `[{id, name, count}]` lỗi học sinh cả trung tâm hay mắc (Coach dùng để giao bài cho gia sư) |

- Mục 11: có `attempt_token` thì server tự tính `time_spent_sec` từ lúc gọi mục 10a (bỏ qua số trình duyệt gửi). `late = true` khi thời gian làm vượt giới hạn quá 30 giây. Mã câu không thuộc đề bị bỏ qua; `time_spent_sec` âm được tính là 0 (không báo lỗi, để học sinh không mất bài).

Dự đoán (code thường, không LLM): trung bình có trọng số 3 bài gần nhất (cũ → mới: 1, 2, 3), khoảng = độ lệch chuẩn (tối thiểu 0,5); cần ≥ 2 bài.
