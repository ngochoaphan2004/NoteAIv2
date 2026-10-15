import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.events import watchdog_daemon
from app.core.scheduler import cron_scheduler
from app.core.logging_config import setup_logging
from app.api.v1.flashcards import router as flashcards_router
from app.api.v1.rag import router as rag_router
from app.api.v1.agents import router as agents_router
from app.api.v1.cron import router as cron_router
from app.api.v1.system import router as system_router
from app.api.v1.plans import router as plans_router

# 1. Khởi tạo hệ thống Ghi Log Bền Vững (Persistent Rotating File + Console)
setup_logging()
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

    logger.info("Starting Internal Cron Scheduler Daemon...")
    await cron_scheduler.start()

    yield

    # Dừng hệ thống
    logger.info("Stopping Cron Scheduler...")
    await cron_scheduler.stop()
    logger.info("Stopping Watchdog listener...")
    watchdog_daemon.stop()
    logger.info("NoteAI.v2 Backend shutdown complete.")

app = FastAPI(
    title="NoteAI.v2 - Local Autonomous PKM API",
    description="Backend Gateway & AI Engineering Engine cho hệ thống quản trị tri thức IELTS tự trị",
    version="2.0.0",
    lifespan=lifespan
)

# 2. HTTP Request Logging Middleware (Ghi nhận thời gian phản hồi & mã HTTP vào log)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    # Chỉ log chi tiết các request API, bỏ qua polling docs/favicon nếu cần
    if request.url.path.startswith("/api"):
        logger.info(
            f"HTTP {request.method} {request.url.path} - Status: {response.status_code} ({duration_ms:.1f}ms)"
        )
    return response

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
app.include_router(cron_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(plans_router, prefix="/api/v1")

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
