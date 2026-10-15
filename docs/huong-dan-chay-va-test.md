# Hướng dẫn chạy, test 

Làm lần lượt từ trên xuống. Mỗi bước có "Đạt khi" để biết đã xong chưa.

## 0. Chuẩn bị (1 lần mỗi máy)

- Cài **Python 3.12** (python.org, nhớ tick "Add to PATH" trên Windows; 3.11 và 3.13 cũng được) và **Node.js 18+** (nodejs.org).
  Đừng dùng Python 3.14, 3.15: nhiều thư viện chưa có bản cài sẵn, `pip install` sẽ đòi "Microsoft Visual C++ Build Tools" rồi lỗi.
  Máy đã có nhiều bản Python (Windows): tạo môi trường bằng `py -3.12 -m venv .venv` thay cho `python -m venv .venv`.

## 1. Cài backend và chạy test (không cần API key)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate              # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```
**Đạt khi:** dòng cuối báo khoảng `36 passed`. Test tự bật chế độ giả (`FAKE_LLM=1`) và dùng database tạm, nên không tốn quota và không đụng dữ liệu thật.

Một test lỗi thì đọc dòng `assert` bị đỏ: nó cho biết hành vi nào đã sai.

## 2. Cấu hình `.env` 

```bash
copy ..\.env.example .env           # Mac/Linux: cp ../.env.example .env
```
Mở `backend/.env`, điền:

| Biến | Điền gì | Bắt buộc? |
|---|---|---|
| `GEMINI_API_KEY` | Key lấy ở https://aistudio.google.com → Get API key | Có (để Nam trả lời thật). Chưa có thì đặt `FAKE_LLM=1` |
| `JWT_SECRET` | Chạy `python -c "import secrets; print(secrets.token_hex(32))"` rồi dán kết quả | Nên đặt ngay; bắt buộc khi deploy |
| `MANAGER_PASSWORD` | Mật khẩu cho tài khoản quản lý `quanly` | Có, nếu muốn xem dashboard |
| `GEMINI_MODEL`, `GEMINI_MODEL_STRONG` | Model cho chat (mặc định `gemini-flash-lite-latest`, nhanh) và cho chấm điểm + Coach (mặc định `gemini-flash-latest`) | Không |

## 3. Chạy backend thật

```bash
uvicorn app.main:app --reload
```
Mở http://localhost:8000/docs.
**Đạt khi:** `GET /api/health` trả `"has_gemini_key": true`.

### Lỗi hay gặp khi chạy thật

| Thấy gì | Nghĩa là | Làm gì |
|---|---|---|
| `503` có chữ `404 NOT_FOUND` hoặc `model ... is no longer available` | Tên model trong `.env` đã bị Google ngừng | Đổi `GEMINI_MODEL`, `GEMINI_MODEL_STRONG` sang tên mới (thông báo lỗi thường gợi ý tên, hoặc xem trong AI Studio) rồi khởi động lại server |
| `503` có chữ `429` hoặc `RESOURCE_EXHAUSTED` | Hết quota miễn phí | Đợi vài phút, hoặc dùng key của thành viên khác; khi chỉ sửa code thì bật `FAKE_LLM=1` |
| `503` có chữ `API key not valid` | Sai key | Kiểm tra dòng `GEMINI_API_KEY` không thừa dấu cách, dấu ngoặc kép |
| `401` "Phiên đăng nhập đã hết hạn" | Server khởi động lại khi chưa đặt `JWT_SECRET` | Đăng nhập lại; đặt `JWT_SECRET` trong `.env` thì hết |
| `503` có chữ `504 DEADLINE_EXCEEDED` | Model "suy nghĩ" quá lâu | Trong `.env` đặt `GEMINI_THINKING=minimal`, hoặc đổi `GEMINI_MODEL` sang model nhẹ hơn (ví dụ `gemini-flash-lite-latest`), rồi khởi động lại server |
| CLI báo "Server trả lời quá chậm" | Gemini đang chậm/quá tải | Đợi 1 phút rồi chạy lại. Chọn sẵn lỗi sai và tính cách để bỏ qua bước Coach. Coach quá `COACH_BUDGET_SEC` giây sẽ tự dùng luật dự phòng (CLI hiện `Coach (rule)`) |

## 4. Thử học sinh ảo bằng CLI

Mở terminal thứ hai (backend vẫn chạy), đứng ở thư mục gốc repo:
```bash
python cli/chat.py                  # đăng nhập minh / demo1234
```
Làm **5 phiên giảng tốt + 5 phiên cố tình giảng kém**, đổi qua 4 tính cách. CLI hỏi trước "giảng tốt hay kém" để tổng hợp. Ví dụ với lỗi HS-01 (y' = 0 thì kết luận cực trị):

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

## 6. Chưa có (để sau MVP)

- Quên mật khẩu / đổi mật khẩu, khóa tài khoản sau nhiều lần đăng nhập sai.
- Quản lý tạo tài khoản gia sư hàng loạt, gắn gia sư vào từng trung tâm.
- Token đang lưu trong `localStorage` của trình duyệt: đủ cho MVP.
