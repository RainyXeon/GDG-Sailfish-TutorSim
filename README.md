# TutorSim – AI Agent huấn luyện gia sư bằng học sinh ảo

Dự án probation GDG, chủ đề *Agentic AI: Agent of Changes*, lĩnh vực Education.

- **Phân hệ 1 (cốt lõi):** gia sư chat chữa bài cho học sinh ảo "Nam" (mắc lỗi sai có thật), được chấm theo rubric 5 tiêu chí, và Coach Agent tự chọn bài luyện tiếp theo.
- **Phân hệ 2 (bản rút gọn):** học sinh làm đề trắc nghiệm có đồng hồ, mỗi phương án sai gắn mã lỗi, có điểm Toán dự kiến. Lỗi học sinh hay mắc được Coach dùng để giao bài cho gia sư.

## Bộ não hoạt động thế nào

```
Gia sư gõ tin nhắn
  -> 1. Bộ phân loại (Gemini): câu này thỏa "điều kiện hiểu ra" nào? có giải hộ không? có phát biểu toán nào?
  -> SymPy kiểm tra phát biểu toán (sai -> lượt đó không được tính)
  -> 2. State machine (CODE): chua_nhan_ra -> nghi_ngo -> da_hieu, mỗi lượt lên tối đa 1 nấc
  -> 3. Học sinh ảo Nam (Gemini): trả lời đúng tính cách, bị khóa theo trạng thái
Kết thúc buổi
  -> 4. Bộ chấm (Gemini chấm từng tiêu chí + trích bằng chứng; CODE tính điểm tổng, SymPy bắt lỗi thì chinh_xac <= 2)
  -> 5. Coach Agent (Gemini tự gọi tool: hồ sơ gia sư, lỗi học sinh thật hay mắc, danh sách lựa chọn) chọn buổi sau
```
Gemini chỉ làm việc cần hiểu ngôn ngữ; việc cần chắc chắn (học sinh hiểu chưa, đúng sai toán, điểm tổng, dự đoán điểm) do code làm.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `backend/agent/` | Bộ não: `state_machine.py`, `classifier.py`, `math_check.py`, `simulator.py`, `evaluator.py`, `coach.py`, `library.py`, `llm.py` |
| `backend/agent/prompts/` | Prompt dạng `.md`. **Sửa chữ, không cần biết code**, giữ nguyên biến `$ten_bien`. Sửa xong dùng ngay, không cần khởi động lại |
| `backend/app/` | API FastAPI (`main.py`), nghiệp vụ (`services.py`), lưu trữ SQLite (`db.py`), Phân hệ 2 (`exam_service.py`) |
| `backend/tests/` | Test, chạy không cần API key |
| `data/misconceptions/` | Thư viện 58 lỗi sai (`ham_so.csv`, `oxyz.csv`). Điều kiện hiểu ra cách nhau bằng ` \| ` |
| `data/exams/` | Đề luyện Phân hệ 2 (JSON) |
| `cli/` | `chat.py` thử học sinh ảo trong terminal (gọi API), `gate_report.py` tổng hợp cổng kiểm tra |
| `frontend/` | Web React (Vite): 8 màn hình gia sư, học sinh, quản lý |
| `scripts/` | Chuyển Excel lỗi sai -> CSV, Excel câu hỏi -> đề JSON |
| `docs/` | Hợp đồng API, nhật ký sửa prompt |

## Chạy trên máy (lần đầu)

Cần: Python 3.11+, Node.js 18+.

### 1. Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate              # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy ..\.env.example .env           # Mac/Linux: cp ../.env.example .env
# mở backend/.env, điền GEMINI_API_KEY (xem mục "Cần bạn cung cấp")
uvicorn app.main:app --reload       # mở http://localhost:8000/docs
```
Chưa có key? Đặt `FAKE_LLM=1` trong `backend/.env`: Nam trả lời bằng câu soạn sẵn, đủ để thử luồng.

### 2. Thử học sinh ảo bằng terminal (Bước 3: tinh chỉnh prompt)
Mở terminal thứ hai, backend vẫn đang chạy:
```bash
python cli/chat.py
python cli/gate_report.py           # sau khi có >= 10 phiên tốt + 10 phiên kém
```
CLI hiện cả trạng thái ẩn của Nam (điều kiện đã thỏa, số lượt thuyết phục, cờ GIẢI HỘ, lý do, độ trễ). Log mỗi phiên lưu ở `cli/logs/` và **nên commit lên** để cả nhóm cùng tổng hợp.

### 3. Frontend
```bash
cd frontend
npm install
npm run dev                         # mở http://localhost:5173
```
Muốn làm giao diện khi chưa bật backend: tạo `frontend/.env.local` với dòng `VITE_USE_MOCK=1`.

### 4. Test
```bash
cd backend
pytest                              # không cần key, không tốn quota
```

## Cần bạn cung cấp

| Thứ cần | Lấy ở đâu | Điền vào |
|---|---|---|
| **Gemini API key** (bắt buộc để chạy thật) | https://aistudio.google.com → Get API key | `backend/.env`: `GEMINI_API_KEY=...` |
| Tên model (tùy chọn) | AI Studio, mục Models | `GEMINI_MODEL`, `GEMINI_MODEL_STRONG` (mặc định `gemini-2.5-flash`) |
| Lỗi sai đã được giáo viên duyệt | File Excel 56 lỗi, cột `trang_thai` = Đồng ý | `python scripts/xlsx_to_csv.py <file.xlsx>`, rồi đặt `ONLY_APPROVED=1` |

**Không commit file `.env`.** `.gitignore` đã chặn sẵn. Mỗi lượt chat gọi Gemini 2 lần, cuối buổi thêm 2 lần (chấm điểm + Coach).

## Đổi dữ liệu

- **Thêm/sửa lỗi sai:** sửa Excel rồi chạy `python scripts/xlsx_to_csv.py <file.xlsx>` (giữ nguyên cột `geogebra` đã có), hoặc sửa thẳng CSV. Khởi động lại backend.
- **Thêm câu trắc nghiệm:** sửa Excel ngân hàng câu hỏi rồi chạy `python scripts/questions_to_exams.py <file.xlsx>` (thêm `--tat-ca` để lấy cả câu chờ duyệt).
- **Gia sư, học sinh mẫu:** nằm trong `backend/app/db.py` (`SEED_TUTORS`, `SEED_STUDENTS`). Xóa `backend/tutorsim.sqlite3` để tạo lại từ đầu.

## Đưa lên mạng (gợi ý)

- Backend lên Render: Root Directory `backend`, Build `pip install -r requirements.txt`, Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Khai báo `GEMINI_API_KEY`, `DEBUG=0`, `CORS_ORIGINS=<địa chỉ Vercel>` trong Environment.
- Frontend lên Vercel: Root Directory `frontend`, biến `VITE_API_URL=<địa chỉ Render>`.
- Gói miễn phí của Render xóa ổ đĩa mỗi lần khởi động lại, nên SQLite sẽ mất dữ liệu. Đủ cho demo; khi thí điểm thật nên chuyển `app/db.py` sang Postgres (Supabase).

## Quy trình Git

Mỗi việc 1 nhánh (`feature/...`, `fix/...`, `prompt/...`, `data/...`) → Pull Request → ít nhất 1 người duyệt → merge vào `main`. Người viết phải giải thích được code của mình trước khi merge. Sửa prompt thì ghi 1 dòng vào `docs/prompt-log.md`.
