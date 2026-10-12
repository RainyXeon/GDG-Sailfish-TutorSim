"""BỘ CHẤM GIA SƯ (LLM-as-judge): LLM chấm từng tiêu chí + trích bằng chứng; điểm tổng do CODE tính."""
from pydantic import BaseModel

from .library import RUBRIC
from .llm import ask_json, load_prompt
from settings import settings


class Evidence(BaseModel):
    criterion: str
    quote: str
    comment: str


class EvalResult(BaseModel):
    chinh_xac: int
    chan_doan: int
    ro_rang: int
    goi_mo: int
    thai_do: int
    evidence: list[Evidence]
    feedback: str


def rubric_text():
    return "\n".join(f"- {r['key']} ({r['ten']}): " + "; ".join(f"{k} = {v}" for k, v in r["muc"].items()) for r in RUBRIC)


def weighted_total(scores):
    return round(sum(max(1, min(4, int(scores[r["key"]]))) * r["trong_so"] for r in RUBRIC), 2)


def evaluate(transcript_text, misconception, final_state, math_warnings):
    prompt = load_prompt(
        "evaluator", bai_toan=misconception["bai_toan"], loi_giai_sai=misconception["loi_giai_sai"],
        nguyen_nhan_goc=misconception["nguyen_nhan_goc"],
        ket_qua="học sinh đã hiểu ra lỗi" if final_state == "da_hieu" else "học sinh CHƯA hiểu ra lỗi",
        math_check="\n".join(f"- {w}" for w in math_warnings) or "- Không phát hiện phát biểu sai.",
        rubric=rubric_text(), transcript=transcript_text)
    fake = {"chinh_xac": 3, "chan_doan": 3, "ro_rang": 3, "goi_mo": 2, "thai_do": 3,
            "evidence": [{"criterion": "goi_mo", "quote": "(giả)", "comment": "[GIẢ] Nhận xét mẫu."}],
            "feedback": "[GIẢ] Nhận xét mẫu khi chạy FAKE_LLM=1."}
    r = ask_json(prompt, EvalResult, fake=fake, model=settings.model_strong, strong=True)
    scores = {k: max(1, min(4, int(getattr(r, k)))) for k in ("chinh_xac", "chan_doan", "ro_rang", "goi_mo", "thai_do")}
    if math_warnings:
        scores["chinh_xac"] = min(scores["chinh_xac"], 2)  # luật cứng: SymPy bắt lỗi thì không quá 2
    return scores, weighted_total(scores), [e.model_dump() for e in r.evidence], r.feedback
