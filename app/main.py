from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.links import router as links_router
from app.routers.redirect import router as redirect_router
from app.routers.dashboard import router as dashboard_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Shortify API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

app.include_router(
    links_router,
    prefix="/api/v1",
)

app.include_router(
    dashboard_router,
    prefix="/api/v1",
)

app.include_router(
    redirect_router,
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }