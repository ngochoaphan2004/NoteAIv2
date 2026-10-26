import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_session

@pytest.fixture(name="session", scope="function")
def session_fixture():
    """SQLite in-memory engine cho testing — không cần PostgreSQL thật"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Import tất cả models để SQLModel.metadata biết cần tạo table nào
    from app.models.flashcard import Flashcard, ReviewLog
    from app.models.test_attempt import TestAttempt, QuestionAnalysis
    from app.models.telemetry import TelemetryLog
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    """TestClient với DB session được override bằng SQLite in-memory"""
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()
