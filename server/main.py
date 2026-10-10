from fastapi import FastAPI

from database import Base, engine
from middleware import AuthMiddleware, RequestLogMiddleware
from routers import auth, catalog, reports, sessions

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TutorSim API",
    description="REST API cho prototype TutorSim: luyện dạy sửa lỗi Toán với học sinh ảo.",
)

app.add_middleware(AuthMiddleware)
app.add_middleware(RequestLogMiddleware)

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(sessions.router)
app.include_router(reports.router)


@app.get("/")
def read_root():
    return {"message": "TutorSim API - xem /docs de biet cac endpoint"}


@app.get("/health")
def health():
    return {"status": "ok"}
