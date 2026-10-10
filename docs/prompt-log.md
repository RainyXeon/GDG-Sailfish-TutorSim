# Nhật ký sửa prompt và luật của học sinh ảo

Mỗi lần sửa prompt (`backend/agent/prompts/`) hoặc luật (`state_machine.py`, `PERSONAS` trong `library.py`), ghi 1 dòng. Đây là bằng chứng "cải tiến có phương pháp" khi thuyết trình.

| Ngày | Người sửa | File | Sửa gì | Vì sao (lỗi quan sát được) |
|---|---|---|---|---|
| 2026-10-10 | Claude (theo phản hồi của lead) | state_machine.py | Mỗi lượt chỉ lên tối đa 1 nấc; giải hộ chỉ tính 1 điều kiện | Thử "hay cãi": gia sư giảng hết đáp án trong 1 tin, Nam hiểu ngay |
| 2026-10-10 | Claude | library.py (PERSONAS) | Hay cãi, mất gốc cần thêm 1 lượt thuyết phục (extra_turns = 1) | Tính cách chỉ nằm trong prompt thì Gemini không tuân theo |
| 2026-10-10 | Claude | prompts/simulator.md | Chỉ đưa cách thể hiện của đúng tính cách đang dùng; thêm phản ứng gợi ý từ thư viện lỗi | Nam "hay cãi" trả lời quá ngoan |
| 2026-10-10 | Claude | prompts/classifier.md | Trích thêm phát biểu toán để SymPy kiểm tra (gộp vào cùng 1 lần gọi) | Tiêu chí "chính xác" trước đây chỉ dựa vào LLM |
| 2026-10-10 | Claude | llm.py | Tắt cảnh báo function calling của SDK | Cảnh báo tiếng Anh in giữa hội thoại |
