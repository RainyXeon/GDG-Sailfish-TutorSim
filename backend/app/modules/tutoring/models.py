from typing import Literal, Optional

from pydantic import BaseModel


class StartSessionIn(BaseModel):
    chuyen_de: Literal["ham_so", "oxyz"] = "ham_so"
    misconception_id: Optional[str] = None   # bỏ trống -> Coach Agent tự chọn lỗi sai
    persona: Optional[str] = None            # thu_dong | hay_cai | mat_goc | nhanh_nhung_au; bỏ trống -> NGẪU NHIÊN


class MessageIn(BaseModel):
    content: str


class SessionSummaryOut(BaseModel):
    session_id: int
    topic: str
    chuyen_de: str = ""
    chuyen_de_name: str = ""
    persona: str = ""
    persona_name: str = ""
    duration_min: Optional[int] = None    # chỉ có với buổi đã chấm
    total: Optional[float]          # null nếu buổi chưa chấm (chỉ có khi ?include_unfinished=true)
    status: Literal["finished", "in_progress", "abandoned"] = "finished"
    created_at: str


class StartSessionOut(BaseModel):
    session_id: int
    student_name: str
    topic: str
    chuyen_de: str = ""
    problem: str
    student_solution: str
    geogebra_commands: list[str]
    persona: str = ""
    persona_name: str = ""
    persona_random: bool = False          # true = gia sư không chọn, hệ thống chọn ngẫu nhiên


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


class CriterionOut(BaseModel):
    key: str
    name: str                             # tên tiêu chí chuẩn của backend
    weight: float
    score: Optional[int]
    evidence: list[Evidence]


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
    # ---- thêm (v1.7) ----
    criteria: list[CriterionOut] = []
    chuyen_de: str = ""
    topic: str = ""
    persona: str = ""
    persona_name: str = ""
    created_at: str = ""
    finished_at: Optional[str] = None
    duration_min: Optional[int] = None
    next_topic: Optional[str] = None
    next_persona_name: Optional[str] = None
    next_reason: str = ""
    next_source: Optional[str] = None     # agent | rule


class TutorStatsOut(BaseModel):
    tutor_id: int
    name: str
    username: str
    code: str
    sessions_count: int
    avg_total: Optional[float]
    last_session: Optional[str]
    total_minutes: int
    avg_scores: dict[str, float]
    active: bool


class RubricItem(BaseModel):
    key: str
    name: str
    weight: float
    levels: dict[str, str]


class SessionMessage(BaseModel):
    role: Literal["tutor", "student"]
    content: str
    created_at: str
    math_warnings: list[str] = []


class SessionDetailOut(BaseModel):
    session_id: int
    student_name: str
    topic: str
    chuyen_de: str
    persona: str = ""
    persona_name: str = ""
    duration_min: Optional[int] = None
    problem: str
    student_solution: str
    geogebra_commands: list[str]
    status: Literal["in_progress", "finished", "abandoned"]
    student_understood: bool
    created_at: str
    finished_at: Optional[str]
    report_id: Optional[int]
    messages: list[SessionMessage]


class AbandonOut(BaseModel):
    session_id: int
    status: Literal["abandoned"]
