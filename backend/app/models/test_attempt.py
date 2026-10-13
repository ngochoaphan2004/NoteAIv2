import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class TestAttempt(SQLModel, table=True):
    __tablename__ = "test_attempts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(description="Tên bài test (Ví dụ: Cam 18 Test 1 Listening)")
    skill: str = Field(index=True, description="Kỹ năng: listening, reading, writing, speaking")
    source_file: Optional[str] = Field(default=None, index=True, description="Đường dẫn file markdown")
    score: Optional[int] = Field(default=None, description="Số câu đúng (chỉ có khi đủ key)")
    total_questions: Optional[int] = Field(default=None, description="Tổng số câu")
    band_score: Optional[float] = Field(default=None, description="Band score ước lượng chính thức")
    raw_attempt_text: Optional[str] = Field(default=None, description="Nội dung tốc ký gốc của người học")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    questions: List["QuestionAnalysis"] = Relationship(back_populates="attempt", cascade_delete=True)

class QuestionAnalysis(SQLModel, table=True):
    __tablename__ = "question_analyses"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    attempt_id: uuid.UUID = Field(foreign_key="test_attempts.id", index=True)
    question_number: int = Field(description="Số thứ tự câu hỏi")
    user_answer: str = Field(description="Đáp án người học chọn")
    correct_answer: Optional[str] = Field(default=None, description="Đáp án chuẩn (nếu có)")
    is_correct: Optional[bool] = Field(default=None, description="Đúng / Sai")
    trap_type: Optional[str] = Field(default=None, description="Loại bẫy / Nguyên nhân sai")
    analysis: Optional[str] = Field(default=None, description="Phân tích chi tiết và cách khắc phục")

    attempt: Optional[TestAttempt] = Relationship(back_populates="questions")
