import sys
from pathlib import Path

# Allow running directly with `python app/main.py` from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth
from app.core.config import settings
from app.db.session import Base, engine
from app.models import user  # noqa: F401  (register models)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Dev convenience; switch to Alembic migrations for production.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(auth.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
