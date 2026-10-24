from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

# Database Engine
# connect_args={"check_same_thread": False} if SQLite, otherwise standard pool
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "postgresql" in settings.DATABASE_URL:
    connect_args = {"connect_timeout": 10}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True
)

def init_db() -> None:
    """Khởi tạo toàn bộ các bảng trong CSDL nếu chưa tồn tại"""
    # Đăng ký các model vào SQLModel.metadata
    from app.models.flashcard import Flashcard, ReviewLog
    from app.models.test_attempt import TestAttempt, QuestionAnalysis
    from app.models.telemetry import TelemetryLog
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency injection session cho FastAPI endpoints"""
    with Session(engine) as session:
        yield session
