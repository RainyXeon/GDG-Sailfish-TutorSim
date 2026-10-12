from typing import Literal, Optional

from pydantic import BaseModel


class StartSessionIn(BaseModel):
    chuyen_de: Literal["ham_so", "oxyz"] = "ham_so"
    misconception_id: Optional[str] = None   # bỏ trống -> Coach Agent tự chọn
    persona: Optional[str] = None            # bỏ trống -> Coach Agent tự chọn


class MessageIn(BaseModel):
    content: str


class SessionSummaryOut(BaseModel):
    session_id: int
    topic: str
    total: float
    created_at: str


class StartSessionOut(BaseModel):
    session_id: int
    student_name: str
    topic: str
    problem: str
    student_solution: str
    geogebra_commands: list[str]


class MessageOut(BaseModel):
    student_reply: str
    math_warnings: list[str]
    status: Literal["in_progress", "student_understood"]


class FinishOut(BaseModel):
    report_id: int


class Scores(BaseModel):
    chinh_xac: int
    chan_doan: int
    ro_rang: int
    goi_mo: int
    thai_do: int


class Evidence(BaseModel):
    criterion: str
    quote: str
    comment: str


class ReportOut(BaseModel):
    report_id: int
    scores: Scores
    total: float
    evidence: list[Evidence]
    feedback: str
    next_recommendation: str
    next_chuyen_de: str
    next_misconception_id: Optional[str]
    next_persona: Optional[str]
