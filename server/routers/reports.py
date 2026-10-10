"""
Tong hop session -> kiem tra "cong" cuoi Buoc 3 (ported tu prototype/gate_report.py,
nhung doc tu SQLite thay vi quet file JSON trong logs/).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from deps import get_current_user, get_db

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


def _rate(sessions: list[models.PracticeSession]) -> float:
    if not sessions:
        return 0.0
    return sum(1 for s in sessions if s.state == "da_hieu") / len(sessions)


def _avg_total(sessions: list[models.PracticeSession]) -> float | None:
    totals = [s.evaluation.total for s in sessions if s.evaluation]
    return round(sum(totals) / len(totals), 2) if totals else None


@router.get("/gate", response_model=schemas.GateReportOut)
def gate_report(db: Session = Depends(get_db)):
    finished = db.query(models.PracticeSession).filter(models.PracticeSession.status == "finished").all()
    good = [s for s in finished if s.intent == "tot"]
    bad = [s for s in finished if s.intent == "kem"]

    r_bad, r_good = _rate(bad), _rate(good)
    return schemas.GateReportOut(
        total_sessions=len(finished),
        good_sessions=len(good),
        bad_sessions=len(bad),
        bad_still_understood_rate=round(r_bad, 4),
        bad_gate_pass=r_bad <= 0.2,
        good_understood_rate=round(r_good, 4),
        good_gate_pass=r_good >= 0.8,
        avg_total_good=_avg_total(good),
        avg_total_bad=_avg_total(bad),
    )
