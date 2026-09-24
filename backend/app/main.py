"""FindOne FastAPI app — Phase 0–3."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.api.jobs import pages as job_pages
from app.api.jobs import router as jobs_router
from app.api.resumes import router as resumes_router
from app.api.score import router as score_router
from app.api.status import router as status_router
from app.db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    config.get_settings()
    init_db()
    yield


app = FastAPI(title="FindOne", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(status_router)
app.include_router(resumes_router)
app.include_router(score_router)
app.include_router(jobs_router)
app.include_router(job_pages)


@app.get("/")
def hello() -> dict[str, str]:
    return {"product": "FindOne", "see": "/api/status"}


if __name__ == "__main__":
    import uvicorn

    settings = config.get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.findone_host,
        port=settings.findone_port,
    )
