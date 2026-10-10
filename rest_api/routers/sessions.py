"""
Phien luyen tap qua REST, tuong duong luong trong prototype/run_chat.py
nhung tach thanh cac buoc goi API doc lap (1 request = 1 luot gia su noi).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import data
import models
import schemas
from classifier import classify
from deps import get_current_user, get_db
from evaluator import evaluate
from simulator import student_reply
from state_machine import KnowledgeState

router = APIRouter(prefix="/sessions", tags=["sessions"], dependencies=[Depends(get_current_user)])


def _get_owned_session(db: Session, session_id: int, user: models.User) -> models.PracticeSession:
    session = db.get(models.PracticeSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return session


def _misconception_or_400(misconception_id: str) -> dict:
    m = data.find_misconception(misconception_id)
    if m is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown misconception_id")
    return m


def _build_history(session: models.PracticeSession, misconception: dict) -> str:
    history = f"{session.student_name}: (nộp bài) {misconception['loi_giai_sai']}"
    for turn in session.turns:
        history += f"\nGia sư: {turn.tutor_message}\n{session.student_name}: {turn.student_reply}"
    return history


def _to_detail(session: models.PracticeSession) -> schemas.SessionDetail:
    misconception = data.find_misconception(session.misconception_id)
    return schemas.SessionDetail(
        id=session.id,
        misconception_id=session.misconception_id,
        persona_key=session.persona_key,
        intent=session.intent,
        state=session.state,
        status=session.status,
        created_at=session.created_at,
        student_name=session.student_name,
        bai_toan=misconception["bai_toan"],
        loi_giai_sai=misconception["loi_giai_sai"],
        satisfied=sorted(session.satisfied or []),
        turns=[schemas.TurnOut.model_validate(t) for t in session.turns],
        evaluation=schemas.EvaluationOut.model_validate(session.evaluation) if session.evaluation else None,
    )


@router.post("", response_model=schemas.SessionDetail, status_code=status.HTTP_201_CREATED)
def start_session(
    body: schemas.SessionCreateRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _misconception_or_400(body.misconception_id)
    if body.persona_key not in data.PERSONAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown persona_key")

    session = models.PracticeSession(
        user_id=user.id,
        student_name=body.student_name,
        misconception_id=body.misconception_id,
        persona_key=body.persona_key,
        intent=body.intent,
        state="chua_nhan_ra",
        satisfied=[],
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _to_detail(session)


@router.get("", response_model=list[schemas.SessionSummary])
def list_sessions(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return (
        db.query(models.PracticeSession)
        .filter(models.PracticeSession.user_id == user.id)
        .order_by(models.PracticeSession.id.desc())
        .all()
    )


@router.get("/{session_id}", response_model=schemas.SessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    session = _get_owned_session(db, session_id, user)
    return _to_detail(session)


@router.post("/{session_id}/turns", response_model=schemas.TurnOut)
def add_turn(
    session_id: int,
    body: schemas.TurnCreateRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    session = _get_owned_session(db, session_id, user)
    if session.status != "in_progress":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Session already finished")

    misconception = data.find_misconception(session.misconception_id)
    history_before = _build_history(session, misconception)

    result = classify(body.tutor_message, misconception, history_before)

    knowledge = KnowledgeState(len(misconception["dieu_kien_hieu_ra"]))
    knowledge.satisfied = set(session.satisfied or [])
    new_state = knowledge.update(result.satisfied)

    history_with_tutor = history_before + f"\nGia sư: {body.tutor_message}"
    reply = student_reply(
        misconception,
        data.PERSONAS[session.persona_key],
        new_state,
        history_with_tutor,
        session.student_name,
    )

    turn = models.Turn(
        session_id=session.id,
        turn_index=len(session.turns),
        tutor_message=body.tutor_message,
        student_reply=reply,
        state_after=new_state,
        satisfied_this_turn=result.satisfied,
        gives_away_answer=result.gives_away_answer,
        reason=result.reason,
    )
    session.state = new_state
    session.satisfied = sorted(knowledge.satisfied)
    db.add(turn)
    db.add(session)
    db.commit()
    db.refresh(turn)
    return turn


@router.post("/{session_id}/finish", response_model=schemas.EvaluationOut)
def finish_session(session_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    session = _get_owned_session(db, session_id, user)
    if session.status != "in_progress":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Session already finished")
    if not session.turns:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Session has no turns yet")

    misconception = data.find_misconception(session.misconception_id)
    transcript = _build_history(session, misconception)
    result, total = evaluate(transcript, misconception)

    evaluation = models.Evaluation(
        session_id=session.id,
        chinh_xac=result.chinh_xac,
        chan_doan=result.chan_doan,
        ro_rang=result.ro_rang,
        goi_mo=result.goi_mo,
        thai_do=result.thai_do,
        evidence=[e.model_dump() for e in result.evidence],
        feedback=result.feedback,
        total=total,
    )
    session.status = "finished"
    session.finished_at = datetime.now(timezone.utc)
    db.add(evaluation)
    db.add(session)
    db.commit()
    db.refresh(evaluation)
    return evaluation
