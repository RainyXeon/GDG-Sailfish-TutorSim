"""
BỘ PHÂN LOẠI LỜI GIẢNG  (người phụ trách: Tech 2 + Tech 3)
Đọc câu gia sư vừa nói -> cho biết thỏa những "điều kiện để hiểu ra" nào.
"""
from pydantic import BaseModel
from llm import ask_json, load_prompt


class ClassifyResult(BaseModel):
    satisfied: list[int]        # số thứ tự các điều kiện được thỏa TRONG LƯỢT NÀY
    gives_away_answer: bool     # gia sư có nói thẳng đáp án thay vì dẫn dắt không
    reason: str                 # giải thích ngắn, để người thử nghiệm đọc


def classify(tutor_message, misconception, history_text):
    conditions = "\n".join(f"[{i}] {c}" for i, c in enumerate(misconception["dieu_kien_hieu_ra"]))
    prompt = load_prompt(
        "classifier",
        bai_toan=misconception["bai_toan"],
        loi_giai_sai=misconception["loi_giai_sai"],
        conditions=conditions,
        history=history_text or "(chưa có)",
        tutor_message=tutor_message,
    )
    fake = {"satisfied": [0] if "điều kiện cần" in tutor_message else [],
            "gives_away_answer": False, "reason": "[GIẢ]"}
    return ask_json(prompt, ClassifyResult, fake=fake)
