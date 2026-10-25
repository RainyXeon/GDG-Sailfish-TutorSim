"""BỘ PHÂN LOẠI LỜI GIẢNG: câu gia sư vừa nói thỏa điều kiện nào + trích phát biểu toán (1 lần gọi Gemini)."""
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator

from .llm import ask_json, load_prompt


class MathClaim(BaseModel):
    kind: str = Field(default="dao_ham", description="Loại phát biểu toán (dao_ham, cuc_tri, khoang_cach_diem_mat_phang)")
    ham_so: Optional[str] = None
    gia_tri_khang_dinh: Optional[str] = None
    diem: Optional[Any] = None  # Để Any để nhận cả list lẫn str nếu Gemini trả về chuỗi "(1,2,3)"
    mat_phang: Optional[Any] = None

    @model_validator(mode='before')
    @classmethod
    def sanitize_claim(cls, data):
        if isinstance(data, dict):
            # Ép kiểu an toàn nếu diem hoặc mat_phang bị truyền dưới dạng chuỗi
            if isinstance(data.get('diem'), str):
                data['diem'] = [data['diem']]
            if isinstance(data.get('mat_phang'), str):
                data['mat_phang'] = [data['mat_phang']]
        return data


class ClassifyResult(BaseModel):
    satisfied: list[int] = Field(
        default_factory=list, 
        description="Danh sách các điều kiện đã thỏa mãn (chỉ số int). BẮT BUỘC trả về, dùng [] nếu không có."
    )
    gives_away_answer: bool = Field(default=False, description="True nếu gia sư tiết lộ đáp án.")
    reason: str = Field(default="", description="Lý do phân loại.")
    math_claims: list[MathClaim] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def sanitize_classify_data(cls, data):
        """Tiền xử lý dữ liệu phòng thủ trước khi Pydantic validate"""
        if isinstance(data, dict):
            if 'satisfied' not in data or data['satisfied'] is None:
                data['satisfied'] = []
            if 'gives_away_answer' not in data or data['gives_away_answer'] is None:
                data['gives_away_answer'] = False
            if 'reason' not in data or data['reason'] is None:
                data['reason'] = ""
            if 'math_claims' not in data or data['math_claims'] is None:
                data['math_claims'] = []
        return data


def _fake(tutor_message):
    t = tutor_message.lower()
    sat = [i for i, kw in enumerate(["điều kiện cần", "đổi dấu"]) if kw in t]
    return {"satisfied": sat, "gives_away_answer": "đáp án là" in t, "reason": "[GIẢ] dò từ khóa", "math_claims": []}


def classify(tutor_message, misconception, history_text, budget_sec=None):
    conditions = "\n".join(f"[{i}] {c}" for i, c in enumerate(misconception["dieu_kien_hieu_ra"]))
    prompt = load_prompt("classifier", bai_toan=misconception["bai_toan"], loi_giai_sai=misconception["loi_giai_sai"],
                         conditions=conditions, history=history_text or "(chưa có)", tutor_message=tutor_message)
    return ask_json(prompt, ClassifyResult, fake=_fake(tutor_message), budget_sec=budget_sec)