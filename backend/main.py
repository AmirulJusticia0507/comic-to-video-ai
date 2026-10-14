from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.generations import router as generations_router
from app.api.jobs import router as jobs_router
from app.api.panels import router as panels_router
from app.api.projects import router as projects_router
from app.api.uploads import router as uploads_router
from app.api.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Comic-to-Video AI Generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(generations_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(panels_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "comic-to-video-ai"}


@app.get("/health")
def health():
    return {"status": "healthy"}
