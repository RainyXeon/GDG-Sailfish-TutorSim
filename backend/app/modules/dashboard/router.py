from typing import Optional

from fastapi import APIRouter, Depends

from app.modules.auth import require_role
from app.modules.exams import MisconceptionCount

from . import service
from .models import DashboardRow, OverviewOut, TopicRow

router = APIRouter(prefix="/api", tags=["Quản lý trung tâm"])


@router.get("/dashboard", response_model=list[DashboardRow])
def dashboard(q: Optional[str] = None, _=Depends(require_role("manager"))):
    """Bảng gia sư. ?q= tìm theo tên, tên đăng nhập hoặc mã gia sư."""
    return service.tutors_overview(q)


@router.get("/dashboard/overview", response_model=OverviewOut)
def overview(_=Depends(require_role("manager"))):
    """Số liệu tổng: gia sư (đang hoạt động), buổi luyện, điểm TB, bài thi, lượt lỗi, top gia sư, top lỗi (kèm %)."""
    return service.overview()


@router.get("/dashboard/topics", response_model=list[TopicRow])
def topics(chuyen_de: Optional[str] = None, _=Depends(require_role("manager"))):
    """Thống kê theo chuyên đề (dang_bai = null) và theo từng dạng bài. ?chuyen_de=ham_so để lọc."""
    return service.topics(chuyen_de)


@router.get("/insights/misconceptions", response_model=list[MisconceptionCount])
def insights_misconceptions(_=Depends(require_role("manager"))):
    return service.center_misconceptions()
