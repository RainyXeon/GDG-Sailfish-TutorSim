"""
BO PHAN LOAI LOI GIANG (ported tu prototype/classifier.py)
Doc cau gia su vua noi -> cho biet thoa nhung "dieu kien de hieu ra" nao.
"""
from pydantic import BaseModel
from llm import ask_json, load_prompt


class ClassifyResult(BaseModel):
    satisfied: list[int]        # so thu tu cac dieu kien duoc thoa TRONG LUOT NAY
    gives_away_answer: bool     # gia su co noi thang dap an thay vi dan dat khong
    reason: str                 # giai thich ngan, de nguoi thu nghiem doc


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
