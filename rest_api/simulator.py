"""
HOC SINH AO (ported tu prototype/simulator.py)
Sinh cau tra loi tu nhien, BI RANG BUOC boi trang thai hieu do state machine quyet dinh.
"""
from llm import ask_text, load_prompt
from state_machine import CHUA_NHAN_RA, NGHI_NGO, DA_HIEU

STATE_GUIDE = {
    CHUA_NHAN_RA: "Em vẫn tin lời giải của mình là đúng. TUYỆT ĐỐI KHÔNG tự nhận ra lỗi, "
                  "không tự sửa, không nói ra lời giải đúng. Có thể hỏi lại, hoặc bảo vệ lời giải theo đúng tính cách.",
    NGHI_NGO: "Em bắt đầu thấy có gì đó chưa ổn nhưng CHƯA hiểu hết. Hãy nói ra chỗ còn băn khoăn hoặc hỏi lại. "
              "KHÔNG được tự nói ra lời giải đúng hoàn chỉnh.",
    DA_HIEU: "Em đã hiểu ra lỗi sai. Hãy tự diễn đạt lại bằng lời của học sinh lớp 12: mình sai ở đâu và làm đúng thế nào.",
}


def student_reply(misconception, persona_desc, state, history_text, student_name="Nam"):
    prompt = load_prompt(
        "simulator",
        student_name=student_name,
        persona=persona_desc,
        bai_toan=misconception["bai_toan"],
        loi_giai_sai=misconception["loi_giai_sai"],
        state_guide=STATE_GUIDE[state],
        history=history_text,
    )
    fake = {CHUA_NHAN_RA: "[GIẢ] Nhưng em thấy mình làm đúng mà?",
            NGHI_NGO: "[GIẢ] Ơ... vậy là chưa chắc ạ?",
            DA_HIEU: "[GIẢ] À em hiểu rồi ạ!"}[state]
    return ask_text(prompt, fake=fake)
