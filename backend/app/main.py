"""
TutorSim API (FastAPI) theo kiểu MODULAR MONOLITH: một ứng dụng, chia thành các module độc lập.
Tài liệu API: docs/api.md
Chạy (đứng trong thư mục backend):  uvicorn app.main:app --reload    -> mở http://localhost:8000/docs
File này CHỈ ghép các module lại; nghiệp vụ nằm trong app/modules/*, bộ não AI nằm trong agent/.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from settings import settings

from .core.errors import ServiceError
from .modules.auth.router import router as auth_router
from .modules.dashboard.router import router as dashboard_router
from .modules.exams.router import router as exams_router
from .modules.tutoring.router import router as tutoring_router

app = FastAPI(title="TutorSim API", version="1.7")
print(settings.cors_origins)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(ServiceError)
def _service_error(_: Request, e: ServiceError):
    headers = {"Retry-After": str(e.retry_after)} if e.retry_after else None
    return JSONResponse(status_code=e.status, content={"detail": e.message}, headers=headers)

@app.get("/api/health", tags=["Hệ thống"])
def health():
    return {"ok": True, "fake_llm": settings.fake_llm, "debug": settings.debug,
            "has_gemini_key": bool(settings.gemini_api_key), "allow_register": settings.allow_register}


for r in (auth_router, tutoring_router, exams_router, dashboard_router):
    app.include_router(r)

app.mount("/", StaticFiles(directory="./frontend", html=True), name="static")
