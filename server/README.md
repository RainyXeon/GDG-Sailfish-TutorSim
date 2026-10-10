# TutorSim REST API

Bản REST API (FastAPI) của `prototype/`, cùng logic học sinh ảo / state machine /
classifier / evaluator, nhưng chạy qua HTTP, có đăng nhập username+password và
lưu dữ liệu vào SQLite thay vì file JSON trong `logs/`.

## Cài đặt
```
cd rest_api
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # rồi điền GEMINI_API_KEY, SECRET_KEY...
```

## Chạy
```
FAKE_LLM=1 uvicorn main:app --reload   # không tốn quota Gemini
uvicorn main:app --reload              # dùng Gemini thật
```
Mở `http://127.0.0.1:8000/docs` để xem/thử toàn bộ API (Swagger UI).

Database SQLite (`app.db`) được tạo tự động cạnh `main.py` khi app khởi động.

## Xác thực
Mọi endpoint (trừ `/`, `/health`, `/auth/register`, `/auth/login`, `/docs`,
`/openapi.json`) đều bị `AuthMiddleware` (xem `middleware.py`) chặn nếu thiếu
header `Authorization: Bearer <token>`.

1. `POST /auth/register` `{"username": "...", "password": "..."}` -> tạo user (mật khẩu băm bcrypt, lưu SQLite).
2. `POST /auth/login` cùng body -> trả `{"access_token": "...", "token_type": "bearer"}` (JWT, hạn `ACCESS_TOKEN_EXPIRE_MINUTES`).
3. Gọi các endpoint còn lại với header `Authorization: Bearer <access_token>`.
4. `GET /auth/me` -> thông tin user hiện tại.

## Luồng luyện tập (tương đương `run_chat.py`)
1. `GET /catalog/misconceptions`, `GET /catalog/personas` -> chọn lỗi sai + tính cách học sinh.
2. `POST /sessions` `{"misconception_id", "persona_key", "intent": "tot"|"kem", "student_name"}` -> mở phiên, trả về đề bài + lời giải sai.
3. `POST /sessions/{id}/turns` `{"tutor_message": "..."}` -> 1 lượt gia sư nói; trả về câu trả lời của học sinh ảo, trạng thái hiểu mới, lý do phân loại (dùng `classifier.py` + `state_machine.py` + `simulator.py` không đổi so với prototype).
4. Lặp lại bước 3 cho đến khi thấy đủ, rồi `POST /sessions/{id}/finish` -> chấm điểm bằng `evaluator.py`, lưu `Evaluation` vào SQLite.
5. `GET /sessions`, `GET /sessions/{id}` -> xem lại lịch sử phiên của mình.

## Gate report (tương đương `gate_report.py`)
`GET /reports/gate` -> tổng hợp TẤT CẢ phiên đã `finish` trong SQLite (không phân biệt
người tạo, giống việc gộp cả thư mục `logs/` cũ): tỉ lệ "giảng kém mà học sinh vẫn hiểu"
(cần <= 20%), tỉ lệ "giảng tốt mà học sinh hiểu" (cần >= 80%), điểm trung bình mỗi nhóm.

## File nào làm gì
| File | Giống prototype nào | Khác gì |
|---|---|---|
| `data.py`, `state_machine.py`, `llm.py`, `classifier.py`, `simulator.py`, `evaluator.py` | file cùng tên trong `prototype/` | logic giữ nguyên, chỉ thêm `find_misconception()` |
| `prompts/*.md` | `prototype/prompts/*.md` | copy nguyên văn |
| `models.py`, `database.py` | `logs/*.json` + `gate_report.py` | thay file JSON bằng bảng SQLite (`users`, `practice_sessions`, `turns`, `evaluations`) |
| `security.py`, `middleware.py`, `deps.py` | (mới) | băm mật khẩu (bcrypt), JWT, middleware chặn request chưa đăng nhập |
| `routers/` | `run_chat.py` + `gate_report.py` | expose luồng đó qua REST endpoint |

Sửa prompt vẫn không cần biết code: mở `prompts/*.md`, giữ nguyên các biến `$ten_bien`.
