from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.firebase import init_firebase
from app.core.redis import close_redis

from app.users.router import router as users_router
from app.wardrobe.router import router as wardrobe_router
from app.recommendations.router import router as recommendations_router
from app.visualizations.router import router as visualizations_router
from app.analytics.router import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_firebase()

    # Precompute CLIP label embeddings in background (non-blocking)
    import asyncio
    from app.ai.clip_service import precompute_label_embeddings
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, precompute_label_embeddings)

    yield

    # Shutdown
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Smart Wardrobe and Fashion Assistant API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers under /api/v1
PREFIX = settings.API_V1_PREFIX
app.include_router(users_router, prefix=PREFIX)
app.include_router(wardrobe_router, prefix=PREFIX)
app.include_router(recommendations_router, prefix=PREFIX)
app.include_router(visualizations_router, prefix=PREFIX)
app.include_router(analytics_router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.APP_NAME}
