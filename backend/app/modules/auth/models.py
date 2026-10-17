from typing import Literal

from pydantic import BaseModel


class RegisterIn(BaseModel):
    username: str
    password: str
    name: str
    role: Literal["tutor", "student"]


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str
    code: str = ""              # mã hiển thị: GS-0001 (gia sư), HV-0004 (học sinh), QL-0006 (quản lý)
    created_at: str


class AuthOut(BaseModel):
    token: str
    user: UserOut


class PersonOut(BaseModel):
    id: int
    name: str
    username: str = ""
    code: str = ""


class ProfileIn(BaseModel):
    name: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


class ForgotIn(BaseModel):
    username: str


class ResetPasswordIn(BaseModel):
    new_password: str


class OkOut(BaseModel):
    ok: bool
    message: str = ""


class ResetRequestOut(BaseModel):
    request_id: int
    user_id: int
    username: str
    name: str
    role: str
    code: str
    created_at: str
