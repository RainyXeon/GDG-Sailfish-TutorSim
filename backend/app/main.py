"""
TutorSim API (FastAPI). Hợp đồng: docs/api-contract.md
Chạy (đứng trong thư mục backend):  uvicorn app.main:app --reload    -> mở http://localhost:8000/docs
File này chỉ nhận/trả dữ liệu; mọi logic ở app/services.py và agent/.
"""
from typing import Literal, Optional

from fastapi import Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from settings import settings

from . import services as S
from .security import decode_token

app = FastAPI(title="TutorSim API", version="1.4")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(S.ServiceError)
def _service_error(_: Request, e: S.ServiceError):
    return JSONResponse(status_code=e.status, content={"detail": e.message})


# ================== Đăng nhập & phân quyền ==================
def current_user(authorization: Optional[str] = Header(default=None)):
    """Đọc 'Authorization: Bearer <token>'. Sai / thiếu / hết hạn -> 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise S.ServiceError(401, "Chưa đăng nhập")
    uid = decode_token(authorization.split(" ", 1)[1].strip())
    user = S.get_user(uid) if uid else None
    if not user:
        raise S.ServiceError(401, "Phiên đăng nhập đã hết hạn, hãy đăng nhập lại")
    return user


def role(*allowed):
    def dep(user=Depends(current_user)):
        if user["role"] not in allowed:
            raise S.ServiceError(403, "Tài khoản của bạn không có quyền dùng chức năng này")
        return user
    return dep


def self_or_manager(user, owner_id):
    if user["role"] != "manager" and user["id"] != owner_id:
        raise S.ServiceError(403, "Bạn chỉ xem được dữ liệu của chính mình")


class RegisterIn(BaseModel):
    username: str
    password: str
    name: str
    role: Literal["tutor", "student"]


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str
    created_at: str


class AuthOut(BaseModel):
    token: str
    user: UserOut


# ================== Dữ liệu gửi lên ==================
class StartSessionIn(BaseModel):
    chuyen_de: Literal["ham_so", "oxyz"] = "ham_so"
    misconception_id: Optional[str] = None   # bỏ trống -> Coach Agent tự chọn
    persona: Optional[str] = None            # bỏ trống -> Coach Agent tự chọn


class MessageIn(BaseModel):
    content: str


class AttemptIn(BaseModel):
    exam_id: str
    answers: dict[str, Optional[Literal["A", "B", "C", "D"]]]
    time_spent_sec: int


# ================== Dữ liệu trả về (hợp đồng) ==================
class TutorOut(BaseModel):
    id: int
    name: str


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


class DashboardRow(BaseModel):
    tutor_id: int
    name: str
    sessions_count: int
    avg_total: Optional[float]
    last_session: Optional[str]


class StudentOut(BaseModel):
    id: int
    name: str


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


# ================== TÀI KHOẢN ==================
@app.get("/", include_in_schema=False)
def root():
    """Mở http://localhost:8000 sẽ tự chuyển sang trang thử API."""
    return RedirectResponse("/docs")


@app.get("/api/health")
def health():
    return {"ok": True, "fake_llm": settings.fake_llm, "debug": settings.debug,
            "has_gemini_key": bool(settings.gemini_api_key), "allow_register": settings.allow_register}


@app.post("/api/auth/register", response_model=AuthOut)
def register(body: RegisterIn):
    return S.register(body.username, body.password, body.name, body.role)


@app.post("/api/auth/login", response_model=AuthOut)
def login(body: LoginIn):
    return S.login(body.username, body.password)


@app.get("/api/auth/me", response_model=UserOut)
def me(user=Depends(current_user)):
    return user


# ================== PHÂN HỆ 1: GIA SƯ ==================
@app.get("/api/tutors", response_model=list[TutorOut])
def list_tutors(_=Depends(role("manager"))):
    return S.list_tutors()


@app.get("/api/tutors/{tutor_id}/sessions", response_model=list[SessionSummaryOut])
def tutor_sessions(tutor_id: int, user=Depends(role("tutor", "manager"))):
    self_or_manager(user, tutor_id)
    return S.tutor_sessions(tutor_id)


@app.post("/api/sessions", response_model=StartSessionOut)
def start_session(body: StartSessionIn, user=Depends(role("tutor"))):
    return S.start_session(user["id"], body.chuyen_de, body.misconception_id, body.persona)


@app.post("/api/sessions/{session_id}/messages", response_model=MessageOut)
def send_message(session_id: int, body: MessageIn, user=Depends(role("tutor"))):
    S.check_session_access(user, session_id)
    return S.send_message(session_id, body.content)


@app.post("/api/sessions/{session_id}/finish", response_model=FinishOut)
def finish_session(session_id: int, user=Depends(role("tutor"))):
    S.check_session_access(user, session_id)
    return S.finish_session(session_id)


@app.get("/api/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: int, user=Depends(role("tutor", "manager"))):
    S.check_session_access(user, report_id)
    return S.get_report(report_id)


@app.get("/api/dashboard", response_model=list[DashboardRow])
def dashboard(_=Depends(role("manager"))):
    return S.dashboard()


@app.get("/api/sessions/{session_id}/debug")
def session_debug(session_id: int, user=Depends(role("tutor", "manager"))):
    """Chỉ khi DEBUG=1: trạng thái ẩn của học sinh ảo, dùng cho CLI tinh chỉnh prompt."""
    S.check_session_access(user, session_id)
    return S.session_debug(session_id)


@app.get("/api/misconceptions")
def list_misconceptions(chuyen_de: Optional[str] = None, _=Depends(current_user)):
    return S.list_misconceptions(chuyen_de)


@app.get("/api/personas")
def list_personas(_=Depends(current_user)):
    return S.list_personas()


# ================== PHÂN HỆ 2: HỌC SINH ==================
@app.get("/api/students", response_model=list[StudentOut])
def list_students(_=Depends(role("manager"))):
    return S.list_students()


@app.get("/api/exams", response_model=list[ExamListItem])
def list_exams(_=Depends(current_user)):
    return S.list_exams()


@app.get("/api/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: str, _=Depends(current_user)):
    return S.get_exam(exam_id)


@app.post("/api/attempts", response_model=AttemptOut)
def submit_attempt(body: AttemptIn, user=Depends(role("student"))):
    return S.submit_attempt(user["id"], body.exam_id, body.answers, body.time_spent_sec)


@app.get("/api/students/{student_id}/summary", response_model=StudentSummaryOut)
def student_summary(student_id: int, user=Depends(role("student", "manager"))):
    self_or_manager(user, student_id)
    return S.student_summary(student_id)


@app.get("/api/insights/misconceptions", response_model=list[MisconceptionCount])
def insights_misconceptions(_=Depends(role("manager"))):
    return S.center_top_misconceptions()
