# TutorSim CLI

Thay thế `prototype/` để thử nghiệm trong terminal. CLI **không có "bộ não" riêng**:
mọi logic (state machine, phân loại, học sinh ảo, chấm điểm) chạy trên `rest_api/`,
CLI chỉ gọi API. Sửa logic/prompt thì sửa trong `rest_api/`, chỉ còn 1 engine.

## Cài đặt
Không cần cài gì thêm, chỉ cần Python 3.9+ (chỉ dùng thư viện chuẩn).

## Chạy
1. Bật server (terminal 1):
   ```
   cd rest_api
   FAKE_LLM=1 uvicorn main:app --reload   # thử luồng, không tốn quota
   uvicorn main:app --reload              # Gemini thật
   ```
2. Dùng CLI (terminal 2):

| Lệnh | Tương đương prototype | Để làm gì |
|---|---|---|
| `python run_chat.py` | `run_chat.py` | Chat với học sinh ảo, gõ `q` để kết thúc và chấm điểm |
| `python run_chat.py --relogin` | | Đăng nhập lại bằng tài khoản khác |
| `python gate_report.py` | `gate_report.py` | Kiểm tra "cổng" cuối Bước 3 (tính trên server, gộp mọi người thử nghiệm) |
| `python sessions.py` / `python sessions.py 12` | đọc file trong `logs/` | Xem danh sách phiên / xem lại 1 phiên |

Lần đầu chạy, CLI hỏi tên đăng nhập + mật khẩu (chưa có thì tự đề nghị tạo tài khoản).
Tên đăng nhập chính là "tên người thử nghiệm". Token được lưu ở `cli/.token` (không commit).

Mỗi phiên chấm xong vẫn lưu thêm 1 file JSON vào `cli/logs/` (cùng định dạng prototype) để đọc bằng mắt.

## Biến môi trường (không bắt buộc)
| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `TUTORSIM_API_URL` | `http://127.0.0.1:8000` | Địa chỉ server |
| `TUTORSIM_USER`, `TUTORSIM_PASSWORD` | (hỏi trong terminal) | Đăng nhập không cần gõ tay |

## Khác prototype
- Dòng theo dõi không còn hiện "lượt thuyết phục x/y" vì API chưa trả về số này.
- Server phải đang chạy; phiên bị dừng giữa chừng (Ctrl+C) vẫn nằm trên server ở trạng thái `in_progress`.
