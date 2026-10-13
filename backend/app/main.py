import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.events import watchdog_daemon
from app.api.v1.flashcards import router as flashcards_router
from app.api.v1.rag import router as rag_router
from app.api.v1.agents import router as agents_router

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("noteai_main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động hệ thống
    logger.info("Initializing NoteAI.v2 Database tables...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database init deferred (container may still be starting): {e}")

    logger.info("Starting Watchdog background file listener...")
    watchdog_daemon.start()

    yield

    # Dừng hệ thống
    logger.info("Stopping Watchdog listener...")
    watchdog_daemon.stop()
    logger.info("NoteAI.v2 Backend shutdown complete.")

app = FastAPI(
    title="NoteAI.v2 - Local Autonomous PKM API",
    description="Backend Gateway & AI Engineering Engine cho hệ thống quản trị tri thức IELTS tự trị",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware cho Vite SPA & Quartz
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8088",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8088",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các API Routers
app.include_router(flashcards_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {
        "app": "NoteAI.v2 - Local Autonomous PKM",
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "ports": {
            "backend": settings.PORT,
            "database_pg": 5433,
            "qdrant": 6333,
            "frontend_spa": 5173
        }
    }
