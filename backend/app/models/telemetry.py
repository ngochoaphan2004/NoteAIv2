import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

class TelemetryLog(SQLModel, table=True):
    __tablename__ = "telemetry_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_name: str = Field(index=True, description="Tên Agent: EvaluatorAgent, PlanningAgent...")
    action: str = Field(description="Hành động: evaluate_test, generate_plan, rag_query...")
    model_name: str = Field(description="Mô hình LLM: gemini-1.5-flash...")
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    latency_ms: float = Field(description="Độ trễ tính bằng mili-giây")
    cost_usd: float = Field(default=0.0, description="Chi phí ước tính ($)")
    status: str = Field(default="success", description="success | error")
    error_message: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
