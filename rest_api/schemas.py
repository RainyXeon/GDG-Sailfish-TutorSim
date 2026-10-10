from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---- auth ----
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


# ---- catalog ----
class MisconceptionSummary(BaseModel):
    id: str
    chuyen_de: str
    ten_loi: str


class MisconceptionDetail(MisconceptionSummary):
    bai_toan: str
    loi_giai_sai: str


class PersonaOut(BaseModel):
    key: str
    description: str


# ---- sessions ----
class SessionCreateRequest(BaseModel):
    misconception_id: str
    persona_key: str
    intent: str = Field(pattern="^(tot|kem)$")
    student_name: str = "Nam"


class TurnCreateRequest(BaseModel):
    tutor_message: str = Field(min_length=1)


class TurnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    turn_index: int
    tutor_message: str
    student_reply: str
    state_after: str
    satisfied_this_turn: list[int]
    gives_away_answer: bool
    reason: str
    created_at: datetime


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chinh_xac: int
    chan_doan: int
    ro_rang: int
    goi_mo: int
    thai_do: int
    evidence: list[dict]
    feedback: str
    total: float


class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    misconception_id: str
    persona_key: str
    intent: str
    state: str
    status: str
    created_at: datetime


class SessionDetail(SessionSummary):
    student_name: str
    bai_toan: str
    loi_giai_sai: str
    satisfied: list[int]
    turns: list[TurnOut]
    evaluation: Optional[EvaluationOut] = None


class GateReportOut(BaseModel):
    total_sessions: int
    good_sessions: int
    bad_sessions: int
    bad_still_understood_rate: float
    bad_gate_pass: bool
    good_understood_rate: float
    good_gate_pass: bool
    avg_total_good: Optional[float]
    avg_total_bad: Optional[float]
