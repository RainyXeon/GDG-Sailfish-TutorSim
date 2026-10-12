from typing import Literal, Optional

from pydantic import BaseModel


class AttemptIn(BaseModel):
    exam_id: str
    answers: dict[str, Optional[Literal["A", "B", "C", "D"]]]
    time_spent_sec: int


class ExamListItem(BaseModel):
    id: str
    title: str
    chuyen_de: str
    num_questions: int
    time_limit_min: int


class QuestionOut(BaseModel):
    id: str
    content: str
    options: dict[str, str]


class ExamOut(BaseModel):
    id: str
    title: str
    time_limit_min: int
    questions: list[QuestionOut]


class QuestionResult(BaseModel):
    question_id: str
    chosen: Optional[str]
    correct_answer: str
    is_correct: bool
    misconception_id: Optional[str]
    misconception_name: Optional[str]
    explanation: str


class AttemptOut(BaseModel):
    attempt_id: int
    exam_title: str
    correct: int
    total: int
    score10: float
    time_spent_sec: int
    results: list[QuestionResult]


class AttemptSummary(BaseModel):
    attempt_id: int
    exam_title: str
    score10: float
    created_at: str


class MisconceptionCount(BaseModel):
    id: str
    name: str
    count: int


class Prediction(BaseModel):
    low: float
    mid: float
    high: float


class StudentSummaryOut(BaseModel):
    attempts: list[AttemptSummary]
    top_misconceptions: list[MisconceptionCount]
    prediction: Optional[Prediction]
    note: str
