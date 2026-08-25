from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.links import router as links_router


app = FastAPI(
    title="Shortify API",
    version="1.0.0",
)


app.include_router(auth_router)

app.include_router(
    links_router,
    prefix="/api/v1",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }