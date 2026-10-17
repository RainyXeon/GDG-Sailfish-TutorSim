from typing import Optional

from fastapi import APIRouter, Depends

from app.core.errors import ServiceError

from app.modules.auth import current_user, get_user, require_role, require_self_or_manager

from . import service
from .models import (AbandonOut, FinishOut, MessageIn, MessageOut, ReportOut, RubricItem, SessionDetailOut,
                     SessionSummaryOut, StartSessionIn, StartSessionOut, TutorStatsOut)

router = APIRouter(prefix="/api", tags=["Phân hệ 1: Gia sư luyện tập"])


@router.get("/tutors/{tutor_id}/sessions", response_model=list[SessionSummaryOut])
def tutor_sessions(tutor_id: int, include_unfinished: bool = False, user=Depends(require_role("tutor", "manager"))):
    """Mặc định chỉ các buổi đã chấm. ?include_unfinished=true: thêm buổi đang dở / đã hủy (total = null)."""
    require_self_or_manager(user, tutor_id)
    return service.tutor_sessions(tutor_id, include_unfinished)


@router.get("/tutors/{tutor_id}/stats", response_model=TutorStatsOut)
def tutor_stats(tutor_id: int, user=Depends(require_role("tutor", "manager"))):
    """Thống kê của một gia sư: số buổi, điểm TB, tổng thời gian, điểm TB từng tiêu chí, còn hoạt động không."""
    require_self_or_manager(user, tutor_id)
    t = get_user(tutor_id)
    if not t or t["role"] != "tutor":
        raise ServiceError(404, "Không tìm thấy gia sư")
    return {"tutor_id": tutor_id, "name": t["name"], "username": t["username"], "code": t["code"],
            **service.tutor_stats(tutor_id)}


@router.get("/rubric", response_model=list[RubricItem])
def rubric(_=Depends(current_user)):
    """5 tiêu chí chấm (tên chuẩn, trọng số, mô tả từng mức 1-4). Frontend nên lấy tên tiêu chí từ đây."""
    return service.rubric()


@router.post("/sessions", response_model=StartSessionOut)
def start_session(body: StartSessionIn, user=Depends(require_role("tutor"))):
    return service.start_session(user["id"], body.chuyen_de, body.misconception_id, body.persona)


@router.get("/sessions/{session_id}", response_model=SessionDetailOut)
def get_session(session_id: int, user=Depends(require_role("tutor", "manager"))):
    """Chi tiết buổi + toàn bộ hội thoại: để làm tiếp buổi dở, hoặc đọc lại hội thoại cạnh báo cáo."""
    service.check_session_access(user, session_id)
    return service.get_session(session_id)


@router.post("/sessions/{session_id}/abandon", response_model=AbandonOut)
def abandon_session(session_id: int, user=Depends(require_role("tutor"))):
    """Gia sư bỏ buổi: đánh dấu hủy, không chấm. Gọi lại nhiều lần vẫn được."""
    service.check_session_access(user, session_id)
    return service.abandon_session(session_id)


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
