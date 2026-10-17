# Hợp đồng API – TutorSim (v1.7)

> v1.7 (chỉ THÊM trường/endpoint, frontend hiện tại không phải sửa; có 1 thay đổi hành vi):
> - **Đổi hành vi:** `POST /api/sessions` bỏ trống `persona` thì tính cách được chọn **ngẫu nhiên** (trước: Coach chọn).
>   Lỗi sai (`misconception_id`) bỏ trống thì vẫn do Coach chọn. Trả thêm `persona`, `persona_name`, `persona_random`, `chuyen_de`.
> - **Tính cách giờ được hiển thị** (theo Figma): có trong lịch sử, chi tiết buổi, báo cáo. Lỗi sai và trạng thái hiểu của Nam vẫn ẩn.
> - **Tiêu chí chấm theo backend:** `GET /api/rubric` (tên chuẩn, trọng số, mô tả mức 1–4); báo cáo có thêm `criteria[]` (tên, điểm nguyên 1–4, dẫn chứng theo tiêu chí).
> - Báo cáo thêm: `topic`, `persona(_name)`, `created_at`, `finished_at`, `duration_min`, `next_topic`, `next_persona_name`, `next_reason`, `next_source`.
> - Lịch sử buổi (mục 2) thêm: `chuyen_de`, `chuyen_de_name`, `persona`, `persona_name`, `duration_min`.
> - `GET /api/tutors/{id}/stats` (gia sư đó, quản lý): số buổi, điểm TB, tổng phút luyện, điểm TB từng tiêu chí, `active`.
> - Tài khoản: `code` (GS-0001 / HV-0004 / QL-0006) trong `/auth/me`; `PATCH /api/auth/me` `{name}`; `POST /api/auth/change-password`
>   `{old_password, new_password}`; quên mật khẩu (không dùng email): `POST /api/auth/forgot-password` `{username}` (công khai) →
>   quản lý xem `GET /api/auth/reset-requests` và đặt mật khẩu mới `POST /api/users/{id}/reset-password` `{new_password}`.
> - Học sinh: câu hỏi có `dang_bai`, `geogebra_commands`; kết quả từng câu có `content`, `options`, `chosen_text`, `correct_text`,
>   `dang_bai`, `misconception_description`; bài làm có `num_wrong`, `num_blank`, `num_misconceptions`; summary có `stats`
>   `{attempts_count, exams_done, avg_score10}` và mỗi bài có `correct`, `total`, `time_spent_sec`.
> - Quản lý: `GET /api/dashboard?q=` (tìm tên / username / mã), mỗi dòng thêm `username, code, total_minutes, active, status_label`;
>   `GET /api/dashboard/overview`; `GET /api/dashboard/topics?chuyen_de=` (theo chuyên đề + từng dạng bài).
>   "Đang hoạt động" = có buổi luyện trong 14 ngày gần nhất, không thì "Tạm nghỉ".


> v1.6 (chỉ THÊM, frontend hiện tại không phải sửa):
> - Mới: `GET /api/sessions/{id}` (chi tiết buổi + hội thoại), `POST /api/sessions/{id}/abandon` (bỏ buổi),
>   `GET /api/tutors/{id}/sessions?include_unfinished=true`, `GET /api/attempts/{id}` (xem lại bài thi),
>   `POST /api/exams/{id}/start` (vé làm bài, tùy chọn).
> - Thêm trường: `status` trong danh sách buổi; `late` trong kết quả bài thi; `attempt_token` (tùy chọn) khi nộp bài.
> - `next_chuyen_de` trong báo cáo giờ lấy theo lỗi sai Coach gợi ý.
> - `POST /api/sessions/{id}/finish` trả về ngay sau khi chấm; Coach Agent chạy ngầm. `GET /api/reports/{id}` chờ Coach
>   tối đa `COACH_WAIT_IN_REPORT_SEC` giây, quá thì dùng luật dự phòng (báo cáo luôn có gợi ý).
> - Tin nhắn và Kết thúc của cùng một buổi chạy lần lượt (không chồng nhau); bấm Kết thúc nhiều lần vẫn trả cùng báo cáo.
> - Lỗi 503 do Gemini có thêm header `Retry-After` (giây) khi biết nên chờ bao lâu. Phiên đã hủy → 409.

> v1.5: chỉ đổi cấu trúc code bên trong (modular monolith). **Đường dẫn, dữ liệu gửi/nhận, phân quyền giữ nguyên v1.4**, frontend và CLI không phải sửa.

- Mọi địa chỉ bắt đầu bằng `/api`, dữ liệu gửi/nhận là JSON. Chạy local: `http://localhost:8000`, thử API: `/docs`.
- Lỗi trả về `{"detail": "lời giải thích"}` với mã 400 (dữ liệu sai), 404 (không có), 409 (phiên đã kết thúc), 503 (Gemini lỗi).
- Muốn đổi hợp đồng: mở Pull Request sửa file này + báo cả nhóm.
- Mọi endpoint (trừ `/api/health`, đăng ký, đăng nhập) cần header `Authorization: Bearer <token>`. Thiếu/sai/hết hạn → 401; sai vai hoặc dữ liệu của người khác → 403.

Thay đổi so với v1.3: thêm đăng nhập JWT và 3 vai (`tutor`, `student`, `manager`). Server lấy người dùng từ token nên **bỏ `tutor_id` khỏi `POST /api/sessions` và `student_id` khỏi `POST /api/attempts`**. `/api/tutors`, `/api/students`, `/api/dashboard`, `/api/insights/misconceptions` chỉ dành cho quản lý.

Thay đổi so với v1.2: `POST /api/sessions` nhận thêm `misconception_id`, `persona` (bỏ trống = Coach Agent chọn); báo cáo có thêm `next_chuyen_de`, `next_misconception_id`, `next_persona`; thêm `/api/health`, `/api/misconceptions`, `/api/personas` và `/api/sessions/{id}/debug` (chỉ khi `DEBUG=1`).

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

**Chỉ khi phát triển** (`DEBUG=1`, gia sư chủ phiên hoặc quản lý, dùng cho `cli/chat.py`): `GET /api/sessions/{id}/debug` → lỗi sai, tính cách, các điều kiện, trạng thái, lựa chọn của Coach (kèm tool đã gọi), và từng lượt (điều kiện thỏa, giải hộ, lý do, phát biểu toán, cảnh báo SymPy, độ trễ). Tắt khi deploy.

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
