from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

import models
from database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    """AuthMiddleware da xac thuc token va gan payload vao request.state.user.
    O day chi can doc lai user tuong ung trong DB."""
    payload = getattr(request.state, "user", None)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    user = db.get(models.User, payload["user_id"])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user
