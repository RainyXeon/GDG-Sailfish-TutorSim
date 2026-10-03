# Prototype "bộ não" TutorSim (Bước 3)

Chạy trong terminal, chưa có giao diện. Mục tiêu: chứng minh học sinh ảo
phản ứng đúng theo mức hiểu và bộ chấm điểm hợp lý, TRƯỚC khi làm web.

## Cài đặt (mỗi người làm 1 lần)
```
cd experiments/prototype
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```
Tạo file `.env` ở thư mục này (KHÔNG commit):
```
GEMINI_API_KEY=key_cua_ban
GEMINI_MODEL=ten_model_lay_trong_AI_Studio
```

## Chạy
| Lệnh | Để làm gì |
|---|---|
| `python math_verifier.py` | Thử SymPy (không cần key) |
| `pytest tests` | Chạy test code thuần (không cần key) |
| `FAKE_LLM=1 python run_chat.py` | Chạy thử luồng bằng câu trả lời giả (không tốn quota). Windows: `set FAKE_LLM=1` rồi `python run_chat.py` |
| `python run_chat.py` | Chat thật với học sinh ảo, gõ `q` để kết thúc và chấm điểm |
| `python gate_report.py` | Tổng hợp các log, kiểm tra "cổng" cuối Bước 3 |

## Ai sửa file nào
| File | Phụ trách | Nội dung |
|---|---|---|
| `data.py` | Tech 5 | Lỗi sai, persona, rubric |
| `state_machine.py`, `llm.py`, `classifier.py` | Tech 2 | Lõi, code thuần + gọi Gemini |
| `prompts/simulator.md`, `simulator.py` | Tech 3 | Học sinh ảo |
| `prompts/evaluator.md`, `evaluator.py` | Tech 4 | Bộ chấm điểm |
| `prompts/classifier.md` | Tech 2 + Tech 3 | Bộ phân loại lời giảng |
| `math_verifier.py`, `tests/`, `gate_report.py` | Tech 7 | Kiểm tra toán, test, tổng hợp |
| `logs/` | Mọi người thử nghiệm | Mỗi phiên chat tự lưu 1 file |

Sửa prompt KHÔNG cần biết code: mở file `.md` trong `prompts/`, sửa chữ, giữ nguyên các biến dạng `$ten_bien`.
Mỗi lần sửa prompt, ghi 1 dòng vào `prompt-log.md`: ngày, ai sửa, sửa gì, vì sao.
