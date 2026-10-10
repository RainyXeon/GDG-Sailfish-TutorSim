# Hướng dẫn chạy, test và những gì team cần tự làm

Làm lần lượt từ trên xuống. Mỗi bước có "Đạt khi" để biết đã xong chưa.

## 0. Chuẩn bị (1 lần mỗi máy)

- Cài **Python 3.11+** (python.org, nhớ tick "Add to PATH" trên Windows) và **Node.js 18+** (nodejs.org).
- Lấy code: `git clone https://github.com/ntanthedev/GDG-Starie.git`, rồi `git checkout claude/hoan-thien-mvp` (hoặc `main` nếu PR đã được merge).

## 1. Cài backend và chạy test (không cần API key)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate              # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```
**Đạt khi:** dòng cuối báo khoảng `33 passed`. Test tự bật chế độ giả (`FAKE_LLM=1`) và dùng database tạm, nên không tốn quota và không đụng dữ liệu thật.

Các nhóm test:

| File | Kiểm tra gì |
|---|---|
| `test_state_machine.py` | Nam không hiểu ngay sau 1 tin; "hay cãi" cần thêm lượt; giải hộ chỉ tính 1 điều kiện; nói sai toán không tiến bộ |
| `test_math_check.py` | SymPy tính đúng đạo hàm, cực trị, khoảng cách; không phạt khi không đọc được biểu thức |
| `test_auth.py` | Băm mật khẩu, JWT, đăng ký sai (trùng tên, mật khẩu ngắn, tự phong quản lý), tài khoản mẫu |
| `test_flow.py` | Một buổi luyện từ đầu đến cuối; Coach ưu tiên lỗi học sinh thật hay mắc; dự đoán điểm; không lộ đáp án |
| `test_api.py` | Đúng hợp đồng API; chưa đăng nhập bị chặn; gia sư không xem được buổi của người khác; chỉ quản lý xem dashboard |

Một test lỗi thì đọc dòng `assert` bị đỏ: nó cho biết hành vi nào đã sai. Chưa hiểu thì chụp màn hình gửi Claude.

## 2. Cấu hình `.env` (việc bạn phải tự làm)

```bash
copy ..\.env.example .env           # Mac/Linux: cp ../.env.example .env
```
Mở `backend/.env`, điền:

| Biến | Điền gì | Bắt buộc? |
|---|---|---|
| `GEMINI_API_KEY` | Key lấy ở https://aistudio.google.com → Get API key | Có (để Nam trả lời thật). Chưa có thì đặt `FAKE_LLM=1` |
| `JWT_SECRET` | Chạy `python -c "import secrets; print(secrets.token_hex(32))"` rồi dán kết quả | Nên đặt ngay; bắt buộc khi deploy |
| `MANAGER_PASSWORD` | Mật khẩu cho tài khoản quản lý `quanly` | Có, nếu muốn xem dashboard |
| `GEMINI_MODEL` | Tên model trong AI Studio, mặc định `gemini-2.5-flash` | Không |

**Không gửi file `.env` cho ai, không commit, không dán key vào chat.** Mỗi thành viên nên dùng key của riêng mình khi thử.

## 3. Chạy backend thật

```bash
uvicorn app.main:app --reload
```
Mở http://localhost:8000/docs.
**Đạt khi:** `GET /api/health` trả `"has_gemini_key": true`.

Thử API trên trang `/docs`:
1. `POST /api/auth/login` với `{"username": "minh", "password": "demo1234"}` → chép `token`.
2. Bấm nút **Authorize** (ổ khóa, góc trên) → dán token → Authorize.
3. Thử `POST /api/sessions` với `{"chuyen_de": "ham_so"}`, rồi `POST /api/sessions/{id}/messages`.

## 4. Thử học sinh ảo bằng CLI (việc quan trọng nhất)

Mở terminal thứ hai (backend vẫn chạy), đứng ở thư mục gốc repo:
```bash
python cli/chat.py                  # đăng nhập minh / demo1234
```
Mỗi người làm **5 phiên giảng tốt + 5 phiên cố tình giảng kém**, đổi qua 4 tính cách. CLI hỏi trước "giảng tốt hay kém" để tổng hợp. Ví dụ với lỗi HS-01 (y' = 0 thì kết luận cực trị):

| Loại | Gia sư nói | Nam nên |
|---|---|---|
| Kém (mơ hồ) | "Sai rồi, em xem lại đi." | Vẫn bảo vệ lời giải |
| Kém (sai kiến thức) | "Đúng rồi, y' = 0 là có cực trị." | Không tiến bộ, SymPy cảnh báo |
| Kém (giải hộ) | Đọc nguyên lời giải đúng một lèo | Có thể "dạ" nhưng không tự giải thích được; cờ GIẢI HỘ |
| Tốt | "Em thử tính y' tại x = −1 và x = 1 xem dấu thế nào?" | Chuyển sang nghi ngờ |
| Tốt (tiếp) | "Vậy y' có đổi dấu khi qua x = 0 không? Muốn có cực trị thì cần gì?" | Hiểu ra (hay cãi, mất gốc cần thêm 1 lượt) |

Sau đó:
```bash
python cli/gate_report.py
```
**Đạt khi:** giảng kém mà Nam vẫn hiểu ≤ 20%, giảng tốt mà Nam hiểu ≥ 80%, điểm hai loại chênh rõ.

Thấy Nam nói chuyện không giống học sinh thật thì sửa ở đâu:

| Hiện tượng | Sửa |
|---|---|
| Giảng mơ hồ mà Nam vẫn tiến bộ | `backend/agent/prompts/classifier.md` (siết quy tắc) |
| Giảng đúng mà Nam mãi không hiểu | `classifier.md` (nới), hoặc cột `dieu_kien_hieu_ra` trong CSV viết quá khắt khe |
| Nam tự sửa lỗi khi chưa đến lúc, nói quá thông minh | `prompts/simulator.md` |
| Tính cách chưa rõ | `cach_the_hien` hoặc `extra_turns` trong `PERSONAS`, file `backend/agent/library.py` |
| Điểm giảng tốt và kém gần bằng nhau | `prompts/evaluator.md`, mô tả mức trong `RUBRIC` (`library.py`) |
| Coach chọn bài vô lý | `prompts/coach.md` |

Sửa prompt xong chat tiếp được ngay. Mỗi lần sửa ghi 1 dòng vào `docs/prompt-log.md`. Commit cả file log trong `cli/logs/`.

## 5. Chạy web

```bash
cd frontend
npm install
npm run dev                         # mở http://localhost:5173
```
Đi thử 3 vai:

| Tài khoản | Mật khẩu | Thấy gì |
|---|---|---|
| `minh` (hoặc tự tạo tài khoản gia sư) | `demo1234` | Trang chủ gia sư → chữa bài → nhận xét → "Luyện theo gợi ý" |
| `ha` | `demo1234` | Trang học sinh → làm đề có đồng hồ → kết quả, điểm dự kiến |
| `quanly` | `MANAGER_PASSWORD` bạn đặt | Bảng theo dõi gia sư + lỗi học sinh hay mắc |

**Đạt khi:** cả 3 vai đi hết luồng không lỗi, và mở "Hình minh họa (GeoGebra)" thấy đồ thị.

## 6. Những gì Claude chưa kiểm tra được (team kiểm giúp)

Môi trường của Claude không gọi được Gemini thật, không cài được gói từ mạng và không tải được GeoGebra. Cần team xác nhận:

- [ ] `pip install` và `npm install` chạy được trên máy (Windows và Mac).
- [ ] Gemini thật trả lời đúng định dạng JSON (nếu lỗi, `cli/chat.py` sẽ in nguyên thông báo, gửi Claude).
- [ ] Coach Agent gọi tool được với model bạn dùng (CLI hiện `Coach (agent)`; nếu luôn là `Coach (rule)` thì Gemini đang lỗi, xem log backend).
- [ ] GeoGebra hiển thị trên trình duyệt.
- [ ] Độ trễ mỗi lượt chat (CLI in `... ms`); nếu quá 6–8 giây, thử model nhẹ hơn.

## 7. Trước khi deploy hoặc thí điểm với người ngoài nhóm

- [ ] `JWT_SECRET` là chuỗi ngẫu nhiên dài, khác nhau giữa máy thử và máy thật.
- [ ] `SEED_DEMO=0` (bỏ tài khoản thử có mật khẩu chung) và `DEBUG=0` (tắt endpoint lộ trạng thái ẩn).
- [ ] `MANAGER_PASSWORD` mạnh, chỉ người phụ trách biết.
- [ ] `CORS_ORIGINS` = đúng địa chỉ web đã deploy.
- [ ] Chỉ dùng lỗi sai đã duyệt: `ONLY_APPROVED=1`.
- [ ] Database: SQLite trên Render miễn phí bị xóa khi khởi động lại. Thí điểm thật thì chuyển `backend/app/db.py` sang Postgres (Supabase), hoặc dùng dịch vụ có ổ đĩa lâu dài.

## 8. Chưa có (để sau MVP)

- Quên mật khẩu / đổi mật khẩu, khóa tài khoản sau nhiều lần đăng nhập sai.
- Quản lý tạo tài khoản gia sư hàng loạt, gắn gia sư vào từng trung tâm.
- Token đang lưu trong `localStorage` của trình duyệt: đủ cho MVP; bản thật nên cân nhắc cookie `HttpOnly`.
