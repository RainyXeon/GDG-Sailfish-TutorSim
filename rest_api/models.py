from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    sessions = relationship("PracticeSession", back_populates="user", cascade="all, delete-orphan")


class PracticeSession(Base):
    """Mot phien luyen tap (tuong duong 1 file log trong prototype/run_chat.py)."""

    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_name = Column(String, default="Nam")
    misconception_id = Column(String, nullable=False)
    persona_key = Column(String, nullable=False)
    intent = Column(String, nullable=False)  # "tot" | "kem"
    state = Column(String, default="chua_nhan_ra")
    satisfied = Column(JSON, default=list)
    status = Column(String, default="in_progress")  # "in_progress" | "finished"
    created_at = Column(DateTime, default=_utcnow)
    finished_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    turns = relationship(
        "Turn", back_populates="session", cascade="all, delete-orphan", order_by="Turn.turn_index"
    )
    evaluation = relationship(
        "Evaluation", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )


class Turn(Base):
    __tablename__ = "turns"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False)
    turn_index = Column(Integer, nullable=False)
    tutor_message = Column(Text, nullable=False)
    student_reply = Column(Text, nullable=False)
    state_after = Column(String, nullable=False)
    satisfied_this_turn = Column(JSON, default=list)
    gives_away_answer = Column(Boolean, default=False)
    reason = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)

    session = relationship("PracticeSession", back_populates="turns")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), unique=True, nullable=False)
    chinh_xac = Column(Integer)
    chan_doan = Column(Integer)
    ro_rang = Column(Integer)
    goi_mo = Column(Integer)
    thai_do = Column(Integer)
    evidence = Column(JSON, default=list)
    feedback = Column(Text, default="")
    total = Column(Float)
    created_at = Column(DateTime, default=_utcnow)

    session = relationship("PracticeSession", back_populates="evaluation")
