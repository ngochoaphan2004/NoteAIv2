import time
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
from app.api.v1.auth import router as auth_router
from app.api.v1.content import router as content_router

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

# CORS Middleware cho Vite SPA & Clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
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
app.include_router(auth_router, prefix="/api/v1")
app.include_router(content_router, prefix="/api/v1")

# Xác định đường dẫn thư mục Frontend build và Audio Assets
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")
INDEX_HTML_PATH = os.path.join(FRONTEND_DIST, "index.html")
ASSETS_DIR = os.path.join(FRONTEND_DIST, "assets")
AUDIO_DIR = os.path.join(PROJECT_ROOT, "content", "assets", "audio")

# 1. Mount Audio Assets tĩnh trực tiếp tại /assets/audio và /content/assets/audio (không cần symlink)
if os.path.isdir(AUDIO_DIR):
    app.mount("/assets/audio", StaticFiles(directory=AUDIO_DIR), name="audio_assets")
    app.mount("/content/assets/audio", StaticFiles(directory=AUDIO_DIR), name="content_audio_assets")

# 2. Mount thư mục tài nguyên JS/CSS của React SPA tại /assets (nếu đã build)
if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="spa_assets")

def get_system_health():
    db_port = 5432 if ":5432" in settings.DATABASE_URL else 5433
    return {
        "app": "NoteAI.v2 - Local Autonomous PKM",
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "ports": {
            "gateway_unified": settings.PORT,
            "database_pg": db_port,
            "qdrant": 6333
        },
        "cloudflare_tunnel": {
            "status": "active",
            "proxy_target": f"http://127.0.0.1:{settings.PORT}"
        }
    }

@app.get("/api/v1/health")
@app.get("/health")
def api_health():
    return get_system_health()

@app.get("/")
def health_check(request: Request):
    # 1. Nếu client yêu cầu JSON rõ ràng (Accept application/json hoặc query ?format=json) -> Trả về JSON health check
    accept = request.headers.get("accept", "")
    if "application/json" in accept or request.query_params.get("format") == "json":
        return get_system_health()

    # 2. Mặc định: Phục vụ Frontend React SPA (index.html) nếu đã build
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)

    # 3. Fallback: Nếu frontend chưa build, trả về JSON health check
    return get_system_health()

# SPA Fallback & Root Static Files Router (phục vụ favicon.ico, logo.svg, icon-*.png và SPA routes)
@app.get("/{full_path:path}")
def serve_spa_or_static(request: Request, full_path: str):
    # Bỏ qua các endpoint API, docs, openapi
    if full_path.startswith(("api/", "docs", "openapi.json")):
        raise HTTPException(status_code=404, detail="Not Found")

    # Phục vụ file tĩnh trực tiếp trong frontend/dist (nếu tồn tại)
    static_file = os.path.join(FRONTEND_DIST, full_path)
    if os.path.isfile(static_file):
        return FileResponse(static_file)

    # Điều hướng toàn bộ SPA routes về index.html
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)

    raise HTTPException(status_code=404, detail="Not Found")
