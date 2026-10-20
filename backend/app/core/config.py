import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = "postgresql://noteai:noteai_secret_password@localhost:5432/noteai_pkm"

    # Qdrant Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "noteai_knowledge"

    # Cloud LLM APIs & Multi-Model Fallback List
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_MODELS: Optional[str] = "gemini-1.5-flash,gemini-2.0-flash,gemini-1.5-flash-8b,gemini-1.5-pro"

    def get_model_list(self) -> list[str]:
        """
        Trả về danh sách các mô hình theo thứ tự ưu tiên (ưu tiên LLM_MODELS, sau đó tới LLM_MODEL).
        Hỗ trợ chuỗi phân tách bởi dấu phẩy, tự động lọc khoảng trắng thừa.
        """
        raw = self.LLM_MODELS or self.LLM_MODEL
        if not raw:
            return ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-8b"]
        models = [m.strip() for m in raw.split(",") if m.strip()]
        return models if models else ["gemini-1.5-flash"]

    # App directories & behavior
    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    CONTENT_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "content"))
    TEMPLATE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates"))
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    WATCHDOG_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        if not os.path.isabs(self.CONTENT_DIR):
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            self.CONTENT_DIR = os.path.abspath(os.path.join(backend_dir, self.CONTENT_DIR))

settings = Settings()
