from typing import Literal, Optional

from pydantic import BaseModel


class AttemptIn(BaseModel):
    exam_id: str
    answers: dict[str, Optional[Literal["A", "B", "C", "D"]]]
    time_spent_sec: int = 0   # số âm (đồng hồ máy bị chỉnh) được tính là 0, không báo lỗi
    attempt_token: Optional[str] = None   # từ POST /api/exams/{id}/start; có thì server tự đo thời gian


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
    dang_bai: str = ""
    geogebra_commands: list[str] = []     # hình minh họa riêng cho câu (rỗng = "Không có đồ thị")


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
    # ---- thêm (v1.7) cho màn Kết quả ----
    content: str = ""
    options: dict[str, str] = {}
    dang_bai: str = ""
    chosen_text: Optional[str] = None
    correct_text: Optional[str] = None
    misconception_description: Optional[str] = None


class AttemptOut(BaseModel):
    attempt_id: int
    exam_title: str
    correct: int
    total: int
    score10: float
    time_spent_sec: int
    late: bool = False              # nộp quá giờ (thời gian làm > giới hạn + 30 giây)
    results: list[QuestionResult]
    exam_id: str = ""
    num_wrong: int = 0              # chọn sai
    num_blank: int = 0              # bỏ trống
    num_misconceptions: int = 0     # số lỗi sai khác nhau nhận diện được


class AttemptDetailOut(AttemptOut):
    student_id: int
    created_at: str


class AttemptStartOut(BaseModel):
    attempt_token: str
    exam_id: str
    time_limit_sec: int


class AttemptSummary(BaseModel):
    attempt_id: int
    exam_id: str = ""
    exam_title: str
    score10: float
    correct: int = 0
    total: int = 0
    time_spent_sec: int = 0
    created_at: str


class MisconceptionCount(BaseModel):
    id: str
    name: str
    count: int


class Prediction(BaseModel):
    low: float
    mid: float
    high: float


class StudentStats(BaseModel):
    attempts_count: int
    exams_done: int                 # số đề khác nhau đã làm ("Đề đã hoàn thành")
    avg_score10: Optional[float]


class StudentSummaryOut(BaseModel):
    attempts: list[AttemptSummary]
    top_misconceptions: list[MisconceptionCount]
    prediction: Optional[Prediction]
    note: str
    stats: Optional[StudentStats] = None
