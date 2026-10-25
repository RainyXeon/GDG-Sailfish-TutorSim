"""BỘ CHẤM GIA SƯ (LLM-as-judge): LLM chấm từng tiêu chí + trích bằng chứng; điểm tổng do CODE tính."""
from pydantic import BaseModel, Field, model_validator

from .library import RUBRIC
from .llm import ask_json, load_prompt
from settings import settings


class Evidence(BaseModel):
    criterion: str = Field(default="", description="Tên tiêu chí (chinh_xac, chan_doan, ro_rang, goi_mo, thai_do)")
    quote: str = Field(default="", description="Trích dẫn đoạn hội thoại")
    comment: str = Field(default="", description="Nhận xét chi tiết")


class EvalResult(BaseModel):
    chinh_xac: int = Field(default=3, description="Điểm chính xác (1-4)")
    chan_doan: int = Field(default=3, description="Điểm chẩn đoán (1-4)")
    ro_rang: int = Field(default=3, description="Điểm rõ ràng (1-4)")
    goi_mo: int = Field(default=3, description="Điểm gợi mở (1-4)")
    thai_do: int = Field(default=3, description="Điểm thái độ (1-4)")
    evidence: list[Evidence] = Field(
        default_factory=list, 
        description="Danh sách trích dẫn bằng chứng. BẮT BUỘC trả về key 'evidence', dùng [] nếu không có."
    )
    feedback: str = Field(default="", description="Nhận xét chung dành cho gia sư")

    @model_validator(mode='before')
    @classmethod
    def sanitize_eval_data(cls, data):
        """Xử lý phòng thủ khi Gemini bỏ sót trường hoặc trả về null."""
        if isinstance(data, dict):
            # Tự động gán mặc định nếu thiếu key hoặc bị null
            if 'evidence' not in data or data['evidence'] is None:
                data['evidence'] = []
            if 'feedback' not in data or data['feedback'] is None:
                data['feedback'] = ""
            
            # Đảm bảo các trường điểm luôn có giá trị số nguyên
            for field in ("chinh_xac", "chan_doan", "ro_rang", "goi_mo", "thai_do"):
                if field not in data or data[field] is None:
                    data[field] = 3
        return data


def rubric_text():
    return "\n".join(f"- {r['key']} ({r['ten']}): " + "; ".join(f"{k} = {v}" for k, v in r["muc"].items()) for r in RUBRIC)


def weighted_total(scores):
    return round(sum(max(1, min(4, int(scores[r["key"]]))) * r["trong_so"] for r in RUBRIC), 2)


def evaluate(transcript_text, misconception, final_state, math_warnings, budget_sec=None):
    prompt = load_prompt(
        "evaluator", bai_toan=misconception["bai_toan"], loi_giai_sai=misconception["loi_giai_sai"],
        nguyen_nhan_goc=misconception["nguyen_nhan_goc"],
        ket_qua="học sinh đã hiểu ra lỗi" if final_state == "da_hieu" else "học sinh CHƯA hiểu ra lỗi",
        math_check="\n".join(f"- {w}" for w in math_warnings) or "- Không phát hiện phát biểu sai.",
        rubric=rubric_text(), transcript=transcript_text)
    fake = {"chinh_xac": 3, "chan_doan": 3, "ro_rang": 3, "goi_mo": 2, "thai_do": 3,
            "evidence": [{"criterion": "goi_mo", "quote": "(giả)", "comment": "[GIẢ] Nhận xét mẫu."}],
            "feedback": "[GIẢ] Nhận xét mẫu khi chạy FAKE_LLM=1."}
    r = ask_json(prompt, EvalResult, fake=fake, model=settings.model_strong, strong=True, budget_sec=budget_sec)
    scores = {k: max(1, min(4, int(getattr(r, k)))) for k in ("chinh_xac", "chan_doan", "ro_rang", "goi_mo", "thai_do")}
    if math_warnings:
        scores["chinh_xac"] = min(scores["chinh_xac"], 2)  # luật cứng: SymPy bắt lỗi thì không quá 2
    return scores, weighted_total(scores), [e.model_dump() for e in r.evidence], r.feedback