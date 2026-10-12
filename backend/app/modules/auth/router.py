from fastapi import APIRouter, Depends

from . import service
from .deps import current_user, require_role
from .models import AuthOut, LoginIn, PersonOut, RegisterIn, UserOut

router = APIRouter(prefix="/api", tags=["Tài khoản"])


@router.post("/auth/register", response_model=AuthOut)
def register(body: RegisterIn):
    return service.register(body.username, body.password, body.name, body.role)


@router.post("/auth/login", response_model=AuthOut)
def login(body: LoginIn):
    return service.login(body.username, body.password)


@router.get("/auth/me", response_model=UserOut)
def me(user=Depends(current_user)):
    return user


@router.get("/tutors", response_model=list[PersonOut])
def list_tutors(_=Depends(require_role("manager"))):
    return service.list_users("tutor")


@router.get("/students", response_model=list[PersonOut])
def list_students(_=Depends(require_role("manager"))):
    return service.list_users("student")
