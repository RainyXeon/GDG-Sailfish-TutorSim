"""
BỘ CHẤM ĐIỂM GIA SƯ - LLM-as-judge  (người phụ trách: Tech 4)
LLM chấm từng tiêu chí + trích bằng chứng. Điểm tổng do CODE tính theo trọng số.
"""
from pydantic import BaseModel
from llm import ask_json, load_prompt
from data import RUBRIC


class Evidence(BaseModel):
    criterion: str
    quote: str      # trích nguyên văn câu trong hội thoại
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
    lines = []
    for r in RUBRIC:
        levels = "; ".join(f"{k} = {v}" for k, v in r["muc"].items())
        lines.append(f"- {r['key']} ({r['ten']}): {levels}")
    return "\n".join(lines)


def evaluate(transcript_text, misconception):
    prompt = load_prompt(
        "evaluator",
        rubric=rubric_text(),
        bai_toan=misconception["bai_toan"],
        loi_giai_sai=misconception["loi_giai_sai"],
        nguyen_nhan_goc=misconception["nguyen_nhan_goc"],
        transcript=transcript_text,
    )
    fake = {"chinh_xac": 3, "chan_doan": 3, "ro_rang": 3, "goi_mo": 2, "thai_do": 3,
            "evidence": [], "feedback": "[GIẢ] Nhận xét mẫu."}
    result = ask_json(prompt, EvalResult, fake=fake)
    total = sum(getattr(result, r["key"]) * r["trong_so"] for r in RUBRIC)  # code tính, không để LLM tính
    return result, round(total, 2)
