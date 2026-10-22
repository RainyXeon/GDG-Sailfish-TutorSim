# TutorSim – AI Agent huấn luyện gia sư bằng học sinh ảo

Dự án probation GDG, chủ đề *Agentic AI: Agent of Changes*, lĩnh vực Education.

- **Phân hệ 1 (cốt lõi):** gia sư chat chữa bài cho học sinh ảo "Nam" (mắc lỗi sai có thật), được chấm theo rubric 5 tiêu chí, và Coach Agent tự chọn bài luyện tiếp theo.
- **Tài khoản:** gia sư, học sinh tự đăng ký; quản lý trung tâm do người phụ trách cấp. Đăng nhập bằng JWT, mỗi người chỉ thấy dữ liệu của mình.
- **Phân hệ 2 (bản rút gọn):** học sinh làm đề trắc nghiệm có đồng hồ, mỗi phương án sai gắn mã lỗi, có điểm Toán dự kiến. Lỗi học sinh hay mắc được Coach dùng để giao bài cho gia sư.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `backend/agent/` | Bộ não: `state_machine.py`, `classifier.py`, `math_check.py`, `simulator.py`, `evaluator.py`, `coach.py`, `library.py`, `llm.py` |
| `backend/agent/prompts/` | Prompt dạng `.md`. **Sửa chữ, không cần biết code**, giữ nguyên biến `$ten_bien`. Sửa xong dùng ngay, không cần khởi động lại |
| `backend/app/main.py` | Chỉ ghép các module lại thành một API FastAPI |
| `backend/app/core/` | Dùng chung: database (`db.py`), mật khẩu + JWT (`security.py`), lỗi nghiệp vụ (`errors.py`) |
| `backend/app/modules/` | Nghiệp vụ, chia module (xem mục **Kiến trúc module** bên dưới) |
| `backend/tests/` | Test, chạy không cần API key |
| `data/misconceptions/` | Thư viện 58 lỗi sai (`ham_so.csv`, `oxyz.csv`). Điều kiện hiểu ra cách nhau bằng ` \| ` |
| `data/exams/` | Đề luyện Phân hệ 2 (JSON) |
| `cli/` | `chat.py` thử học sinh ảo trong terminal (gọi API), `gate_report.py` tổng hợp cổng kiểm tra |
| `frontend/` | Web HTML + CSS + JS: 64 màn hình gia sư, học sinh, quản lý |
| `scripts/` | Chuyển Excel lỗi sai -> CSV, Excel câu hỏi -> đề JSON |
| `docs/` | **Hướng dẫn chạy và test** (`huong-dan-chay-va-test.md`), hợp đồng API, nhật ký sửa prompt |

## Thiết kế giao diện và Frontend

- **Figma:** [TutorSim – UI Screens và Prototype](https://www.figma.com/design/QsuadJi243WJ4oA83m0yKr/TutorSim). Thiết kế có Light Mode và Dark Mode cho Đăng nhập/Đăng ký, Học sinh, Gia sư và Quản lý.
- **Bản tham chiếu khi triển khai:** `HANDOFF • TutorSim UI v1 • 2026-10-16` trong Figma, gồm 64 màn hình chính (32 Light, 32 Dark). Các thay đổi thiết kế về sau cần được nhóm thống nhất trước khi cập nhật bản bàn giao.
- **Trạng thái:** Nhóm đã xác nhận Prototype đạt yêu cầu; phía Backend thông báo đã đủ chức năng. Frontend đang ở giai đoạn chuẩn bị triển khai và cần kiểm thử tích hợp với API thực tế.
- **Quy ước FE:** Dùng Figma Dev Mode để đối chiếu kích thước, màu sắc và component; ưu tiên tái sử dụng giao diện chung, đồng bộ Light/Dark. Vai trò tài khoản do Backend xác thực, không chọn lại sau đăng nhập.

## Kiến trúc module (modular monolith)

Một ứng dụng, một lần chạy (`uvicorn app.main:app`), nhưng nghiệp vụ chia thành các module tách bạch trong `backend/app/modules/`. Mỗi module có cùng khuôn: `__init__.py` (hàm công khai), `service.py` (nghiệp vụ + bảng của module), `router.py` (endpoint), `models.py` (dữ liệu gửi/nhận).

| Module | Làm gì | Bảng sở hữu | Endpoint |
|---|---|---|---|
| `auth` | Đăng ký, đăng nhập, JWT, phân quyền theo vai | `users` | `/api/auth/*`, `/api/tutors`, `/api/students` |
| `tutoring` | Phân hệ 1: buổi luyện với Nam, chấm điểm, báo cáo | `sessions`, `messages`, `reports` | `/api/sessions/*`, `/api/reports/*`, `/api/tutors/{id}/sessions`, `/api/misconceptions`, `/api/personas` |
| `coach` | Chọn bài luyện tiếp theo (Coach Agent + luật dự phòng) | không có | không có (tutoring gọi) |
| `exams` | Phân hệ 2: đề trắc nghiệm, chấm, mã lỗi, dự đoán điểm | `attempts` | `/api/exams/*`, `/api/attempts`, `/api/students/{id}/summary` |
| `dashboard` | Màn quản lý trung tâm, chỉ đọc từ module khác | không có | `/api/dashboard`, `/api/insights/misconceptions` |

Bộ não AI (`backend/agent/`) và prompt vẫn để nguyên chỗ cũ; các module gọi vào đó.

**Hai quy tắc** (test `tests/test_boundaries.py` tự kiểm tra, vi phạm là test đỏ):
1. Module khác chỉ được import hàm công khai: `from app.modules.exams import top_misconceptions_for_center` (đúng), `from app.modules.exams.service import ...` (sai).
2. Module chỉ đọc/ghi bảng của chính mình. Cần dữ liệu module khác thì gọi hàm công khai của nó (ví dụ dashboard gọi `tutoring.tutor_stats()` chứ không tự `SELECT` bảng `reports`).

Thêm module mới: tạo thư mục theo khuôn trên, khai bảng bằng `db.register_schema(...)`, thêm router vào `app/main.py`, thêm bảng vào danh sách trong `tests/test_boundaries.py`.

## Chạy trên máy (lần đầu)

Hướng dẫn đầy đủ từng bước, kèm cách kiểm tra từng phần: **[docs/huong-dan-chay-va-test.md](docs/huong-dan-chay-va-test.md)**. Tóm tắt:

Cần: **Python 3.11, 3.12 hoặc 3.13** (khuyên dùng 3.12; bản quá mới như 3.14, 3.15 thường chưa có sẵn thư viện, `pip install` sẽ lỗi), Node.js 18+.

### 1. Backend
```bash
python -m venv .venv
.venv\Scripts\activate              # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy backend\.env.example backend\.env           # Mac/Linux: cp backend/.env.example backend/.env
# mở backend/.env, điền GEMINI_API_KEY, JWT_SECRET, MANAGER_PASSWORD (xem mục "Cần bạn cung cấp")
uvicorn app.main:app --app-dir backend --reload       # mở http://localhost:8000/docs
```
Chưa có key? Đặt `FAKE_LLM=1` trong `backend/.env`: Nam trả lời bằng câu soạn sẵn, đủ để thử luồng.

### 2. Thử học sinh ảo bằng terminal (Bước 3: tinh chỉnh prompt)
Mở terminal thứ hai, backend vẫn đang chạy:
```bash
python cli/chat.py                  # đăng nhập gia sư: minh / demo1234
python cli/gate_report.py           # sau khi có >= 10 phiên tốt + 10 phiên kém
```
CLI hiện cả trạng thái ẩn của Nam (điều kiện đã thỏa, số lượt thuyết phục, cờ GIẢI HỘ, lý do, độ trễ). Log mỗi phiên lưu ở `cli/logs/` và **nên commit lên** để cả nhóm cùng tổng hợp.

### 3. Frontend

Frontend sẽ chạy cùng backend, có thể truy cập cùng link của backend `http://localhost:8000`

### 4. Test
```bash
pytest backend                              # không cần key, không tốn quota
```