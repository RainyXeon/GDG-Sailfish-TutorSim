"""Middleware lop auth: kiem tra Bearer token cho moi request tru danh sach
cong khai, va gan payload da giai ma vao request.state.user de deps.get_current_user
dung lai (khong giai ma JWT lan thu hai)."""
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from security import decode_access_token

PUBLIC_PATHS = {
    "/",
    "/health",
    "/auth/register",
    "/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)

        token = auth_header[len("Bearer "):]
        try:
            payload = decode_access_token(token)
        except jwt.PyJWTError:
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        request.state.user = payload
        return await call_next(request)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log ngan gon moi request - giup theo doi mot phien luyen tap qua nhieu lan goi API."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        print(f"{request.method} {request.url.path} -> {response.status_code}")
        return response
