"""Kiểm tra đăng nhập + vai cho endpoint của mọi module (dùng với FastAPI Depends)."""
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import ServiceError
from app.core.security import decode_token

from .service import get_user

# HTTPBearer làm hiện nút "Authorize" trên trang /docs để dán token khi thử API
bearer = HTTPBearer(auto_error=False, description="Dán token lấy từ POST /api/auth/login")


def current_user(cred: Optional[HTTPAuthorizationCredentials] = Depends(bearer)):
    """Đọc 'Authorization: Bearer <token>'. Sai / thiếu / hết hạn -> 401."""
    if cred is None or cred.scheme.lower() != "bearer":
        raise ServiceError(401, "Chưa đăng nhập")
    uid = decode_token(cred.credentials.strip())
    user = get_user(uid) if uid else None
    if not user:
        raise ServiceError(401, "Phiên đăng nhập đã hết hạn, hãy đăng nhập lại")
    return user


def require_role(*allowed):
    def dep(user=Depends(current_user)):
        if user["role"] not in allowed:
            raise ServiceError(403, "Tài khoản của bạn không có quyền dùng chức năng này")
        return user
    return dep


def require_self_or_manager(user, owner_id):
    if user["role"] != "manager" and user["id"] != owner_id:
        raise ServiceError(403, "Bạn chỉ xem được dữ liệu của chính mình")
