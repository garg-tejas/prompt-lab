from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import engine, Base
from app.api.v1 import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        # In production use Alembic; this is convenience for dev
        if settings.environment == "development":
            pass  # await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Prompt versioning and evaluation platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)

@app.get("/health", tags=["health"])
async def health_check():
    database = False
    cache = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        database = True
    except Exception:
        database = False
    try:
        from redis.asyncio import from_url

        client = from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
        cache = True
    except Exception:
        cache = False
    body = {
        "status": "ok" if database and cache else "degraded",
        "database": database,
        "redis": cache,
        "environment": settings.environment,
    }
    if not (database and cache):
        return JSONResponse(status_code=503, content=body)
    return body
