from typing import Optional

from fastapi import APIRouter, Depends

from app.modules.auth import current_user, require_role, require_self_or_manager

from . import service
from .models import FinishOut, MessageIn, MessageOut, ReportOut, SessionSummaryOut, StartSessionIn, StartSessionOut

router = APIRouter(prefix="/api", tags=["Phân hệ 1: Gia sư luyện tập"])


@router.get("/tutors/{tutor_id}/sessions", response_model=list[SessionSummaryOut])
def tutor_sessions(tutor_id: int, user=Depends(require_role("tutor", "manager"))):
    require_self_or_manager(user, tutor_id)
    return service.tutor_sessions(tutor_id)


@router.post("/sessions", response_model=StartSessionOut)
def start_session(body: StartSessionIn, user=Depends(require_role("tutor"))):
    return service.start_session(user["id"], body.chuyen_de, body.misconception_id, body.persona)


@router.post("/sessions/{session_id}/messages", response_model=MessageOut)
def send_message(session_id: int, body: MessageIn, user=Depends(require_role("tutor"))):
    service.check_session_access(user, session_id)
    return service.send_message(session_id, body.content)


@router.post("/sessions/{session_id}/finish", response_model=FinishOut)
def finish_session(session_id: int, user=Depends(require_role("tutor"))):
    service.check_session_access(user, session_id)
    return service.finish_session(session_id)


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: int, user=Depends(require_role("tutor", "manager"))):
    service.check_session_access(user, report_id)
    return service.get_report(report_id)


@router.get("/sessions/{session_id}/debug")
def session_debug(session_id: int, user=Depends(require_role("tutor", "manager"))):
    """Chỉ khi DEBUG=1: trạng thái ẩn của học sinh ảo, dùng cho CLI tinh chỉnh prompt."""
    service.check_session_access(user, session_id)
    return service.session_debug(session_id)


@router.get("/misconceptions")
def list_misconceptions(chuyen_de: Optional[str] = None, _=Depends(current_user)):
    return service.list_misconceptions(chuyen_de)


@router.get("/personas")
def list_personas(_=Depends(current_user)):
    return service.list_personas()
