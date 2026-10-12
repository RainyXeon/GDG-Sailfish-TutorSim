from fastapi import APIRouter, Depends

from app.modules.auth import current_user, require_role, require_self_or_manager

from . import service
from .models import AttemptIn, AttemptOut, ExamListItem, ExamOut, StudentSummaryOut

router = APIRouter(prefix="/api", tags=["Phân hệ 2: Học sinh luyện đề"])


@router.get("/exams", response_model=list[ExamListItem])
def list_exams(_=Depends(current_user)):
    return service.list_exams()


@router.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: str, _=Depends(current_user)):
    return service.get_exam(exam_id)


@router.post("/attempts", response_model=AttemptOut)
def submit_attempt(body: AttemptIn, user=Depends(require_role("student"))):
    return service.submit_attempt(user["id"], body.exam_id, body.answers, body.time_spent_sec)


@router.get("/students/{student_id}/summary", response_model=StudentSummaryOut)
def student_summary(student_id: int, user=Depends(require_role("student", "manager"))):
    require_self_or_manager(user, student_id)
    return service.student_summary(student_id)
