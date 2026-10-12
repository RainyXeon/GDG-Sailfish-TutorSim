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
    created_at: str


class AuthOut(BaseModel):
    token: str
    user: UserOut


class PersonOut(BaseModel):
    id: int
    name: str
