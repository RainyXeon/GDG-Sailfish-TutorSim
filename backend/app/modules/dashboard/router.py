from fastapi import APIRouter, Depends

from app.modules.auth import require_role
from app.modules.exams import MisconceptionCount

from . import service
from .models import DashboardRow

router = APIRouter(prefix="/api", tags=["Quản lý trung tâm"])


@router.get("/dashboard", response_model=list[DashboardRow])
def dashboard(_=Depends(require_role("manager"))):
    return service.tutors_overview()


@router.get("/insights/misconceptions", response_model=list[MisconceptionCount])
def insights_misconceptions(_=Depends(require_role("manager"))):
    return service.center_misconceptions()
