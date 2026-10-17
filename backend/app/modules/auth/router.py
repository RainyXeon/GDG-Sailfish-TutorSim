from fastapi import APIRouter, Depends

from . import service
from .deps import current_user, require_role
from .models import (AuthOut, ChangePasswordIn, ForgotIn, LoginIn, OkOut, PersonOut, ProfileIn, RegisterIn,
                     ResetPasswordIn, ResetRequestOut, UserOut)

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


@router.patch("/auth/me", response_model=UserOut)
def update_me(body: ProfileIn, user=Depends(current_user)):
    """Đổi tên hiển thị."""
    return service.update_profile(user["id"], body.name)


@router.post("/auth/change-password", response_model=OkOut)
def change_password(body: ChangePasswordIn, user=Depends(current_user)):
    return service.change_password(user["id"], body.old_password, body.new_password)


@router.post("/auth/forgot-password", response_model=OkOut)
def forgot_password(body: ForgotIn):
    """Công khai. Không có email nên yêu cầu được gửi tới quản lý trung tâm."""
    return service.request_password_reset(body.username)


@router.get("/auth/reset-requests", response_model=list[ResetRequestOut])
def reset_requests(_=Depends(require_role("manager"))):
    """Quản lý: các yêu cầu quên mật khẩu đang chờ."""
    return service.list_reset_requests()


@router.post("/users/{user_id}/reset-password", response_model=OkOut)
def reset_password(user_id: int, body: ResetPasswordIn, _=Depends(require_role("manager"))):
    """Quản lý đặt mật khẩu mới cho gia sư / học sinh."""
    return service.reset_password(user_id, body.new_password)


@router.get("/tutors", response_model=list[PersonOut])
def list_tutors(_=Depends(require_role("manager"))):
    return service.list_users("tutor")


@router.get("/students", response_model=list[PersonOut])
def list_students(_=Depends(require_role("manager"))):
    return service.list_users("student")
