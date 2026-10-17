from typing import Optional

from pydantic import BaseModel


class DashboardRow(BaseModel):
    tutor_id: int
    name: str
    sessions_count: int
    avg_total: Optional[float]
    last_session: Optional[str]
    # ---- thêm (v1.7) ----
    username: str = ""
    code: str = ""                   # GS-0001
    total_minutes: int = 0
    active: bool = False             # có buổi luyện trong 14 ngày gần nhất
    status_label: str = ""           # "Đang hoạt động" | "Tạm nghỉ"


class MisconceptionPercent(BaseModel):
    id: str
    name: str
    count: int
    percent: int


class OverviewOut(BaseModel):
    tutors_count: int
    active_tutors: int
    students_count: int
    sessions_total: int
    sessions_finished: int
    sessions_in_progress: int
    sessions_abandoned: int
    avg_total: Optional[float]
    attempts_count: int
    students_with_attempts: int
    misconception_count: int
    top_tutors: list[DashboardRow]
    top_misconceptions: list[MisconceptionPercent]


class NamedCount(BaseModel):
    id: str
    name: str
    count: int


class TopicRow(BaseModel):
    chuyen_de: str
    dang_bai: Optional[str]          # null = dòng tổng của cả chuyên đề
    label: str                       # "Hàm số" hoặc "Hàm số – Cực trị"
    sessions_count: int
    avg_total: Optional[float]
    tutors_count: int
    practiced_misconceptions: list[NamedCount]
    student_misconception_count: int
    student_top_misconceptions: list[NamedCount]
