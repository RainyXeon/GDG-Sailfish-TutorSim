"""HỌC SINH ẢO: trả lời tự nhiên, BỊ KHÓA theo trạng thái hiểu do state machine quyết định."""
from .llm import ask_text, load_prompt
from .state_machine import CHUA_NHAN_RA, NGHI_NGO, DA_HIEU

STATE_GUIDE = {
    CHUA_NHAN_RA: "Em vẫn tin lời giải của mình là đúng. TUYỆT ĐỐI KHÔNG tự nhận ra lỗi, không tự sửa, "
                  "không nói ra lời giải đúng. Có thể hỏi lại, hoặc bảo vệ lời giải theo đúng tính cách.",
    NGHI_NGO: "Em bắt đầu thấy có gì đó chưa ổn nhưng CHƯA hiểu hết. Nói ra chỗ còn băn khoăn hoặc hỏi lại "
              "(đúng tính cách). KHÔNG được tự nói ra lời giải đúng hoàn chỉnh, không nói 'em hiểu rồi'.",
    DA_HIEU: "Em đã hiểu ra lỗi sai. Tự diễn đạt lại bằng lời học sinh lớp 12: mình sai ở đâu và làm đúng thế nào.",
}
FAKE = {CHUA_NHAN_RA: "[GIẢ] Nhưng em thấy mình làm đúng mà thầy?",
        NGHI_NGO: "[GIẢ] Ơ... vậy là chưa chắc ạ? Thầy giải thích thêm được không?",
        DA_HIEU: "[GIẢ] À em hiểu rồi ạ, em sai ở chỗ đó!"}


def student_reply(misconception, persona, state, history_text, student_name="Nam"):
    prompt = load_prompt("simulator", student_name=student_name, persona=persona["mo_ta"],
                         persona_behavior=persona["cach_the_hien"], bai_toan=misconception["bai_toan"],
                         loi_giai_sai=misconception["loi_giai_sai"],
                         phan_ung="; ".join(misconception.get("phan_ung_goi_y") or []) or "(không có)",
                         state_guide=STATE_GUIDE[state], history=history_text)
    return ask_text(prompt, fake=FAKE[state])
