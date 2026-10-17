from fastapi import APIRouter, Depends

from app.modules.auth import current_user, require_role, require_self_or_manager

from . import service
from .models import AttemptDetailOut, AttemptIn, AttemptOut, AttemptStartOut, ExamListItem, ExamOut, StudentSummaryOut

router = APIRouter(prefix="/api", tags=["Phân hệ 2: Học sinh luyện đề"])


@router.get("/exams", response_model=list[ExamListItem])
def list_exams(_=Depends(current_user)):
    return service.list_exams()


@router.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: str, _=Depends(current_user)):
    return service.get_exam(exam_id)


@router.post("/exams/{exam_id}/start", response_model=AttemptStartOut)
def start_attempt(exam_id: str, user=Depends(require_role("student"))):
    """Tùy chọn: lấy vé làm bài lúc bắt đầu, gửi lại trong POST /api/attempts để server tự đo thời gian."""
    return service.start_attempt(user["id"], exam_id)


@router.post("/attempts", response_model=AttemptOut)
def submit_attempt(body: AttemptIn, user=Depends(require_role("student"))):
    return service.submit_attempt(user["id"], body.exam_id, body.answers, body.time_spent_sec, body.attempt_token)


@router.get("/attempts/{attempt_id}", response_model=AttemptDetailOut)
def get_attempt(attempt_id: int, user=Depends(require_role("student", "manager"))):
    """Xem lại một bài đã nộp (từng câu, đáp án, lỗi sai). Học sinh chỉ xem bài của mình; quản lý xem được hết."""
    a = service.get_attempt(attempt_id)
    require_self_or_manager(user, a["student_id"])
    return a


@router.get("/students/{student_id}/summary", response_model=StudentSummaryOut)
def student_summary(student_id: int, user=Depends(require_role("student", "manager"))):
    require_self_or_manager(user, student_id)
    return service.student_summary(student_id)
