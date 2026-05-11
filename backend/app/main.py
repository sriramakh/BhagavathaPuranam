from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assets, characters, corpus, episodes, health
from app.core.config import get_settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Bhagavatham animated storybook engine with character memory.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(characters.router)
app.include_router(assets.router)
app.include_router(episodes.router)
app.include_router(corpus.router)


@app.get("/")
def root():
    return {"name": settings.app_name, "docs": "/docs"}
