"""BỘ PHÂN LOẠI LỜI GIẢNG: câu gia sư vừa nói thỏa điều kiện nào + trích phát biểu toán (1 lần gọi Gemini)."""
from typing import Literal, Optional
from pydantic import BaseModel

from .llm import ask_json, load_prompt


class MathClaim(BaseModel):
    kind: Literal["dao_ham", "cuc_tri", "khoang_cach_diem_mat_phang"]
    ham_so: Optional[str] = None
    gia_tri_khang_dinh: Optional[str] = None
    diem: Optional[list[float]] = None
    mat_phang: Optional[list[float]] = None


class ClassifyResult(BaseModel):
    satisfied: list[int]
    gives_away_answer: bool
    reason: str
    math_claims: list[MathClaim]  # không đặt mặc định: Gemini luôn trả về (có thể là [])


def _fake(tutor_message):
    t = tutor_message.lower()
    sat = [i for i, kw in enumerate(["điều kiện cần", "đổi dấu"]) if kw in t]
    return {"satisfied": sat, "gives_away_answer": "đáp án là" in t, "reason": "[GIẢ] dò từ khóa", "math_claims": []}


def classify(tutor_message, misconception, history_text, budget_sec=None):
    conditions = "\n".join(f"[{i}] {c}" for i, c in enumerate(misconception["dieu_kien_hieu_ra"]))
    prompt = load_prompt("classifier", bai_toan=misconception["bai_toan"], loi_giai_sai=misconception["loi_giai_sai"],
                         conditions=conditions, history=history_text or "(chưa có)", tutor_message=tutor_message)
    return ask_json(prompt, ClassifyResult, fake=_fake(tutor_message), budget_sec=budget_sec)
