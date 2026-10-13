import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class FlashcardBase(SQLModel):
    front: str = Field(index=True, description="Từ vựng hoặc cụm từ học thuật")
    back: str = Field(description="Nghĩa tiếng Việt và collocations ví dụ")
    ipa: Optional[str] = Field(default=None, description="Phiên âm IPA")
    part_of_speech: Optional[str] = Field(default=None, description="Loại từ (n, v, adj...)")
    synonyms: Optional[str] = Field(default=None, description="Từ đồng nghĩa")
    context: Optional[str] = Field(default=None, description="Ngữ cảnh trong đề thi")
    tags: str = Field(default="ielts", index=True, description="Tags phân loại (ielts, week-01, b2-c1)")
    source_file: Optional[str] = Field(default=None, description="File markdown gốc")

class Flashcard(FlashcardBase, table=True):
    __tablename__ = "flashcards"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    stability: float = Field(default=0.0, description="Độ ổn định S của trí nhớ (tính bằng ngày)")
    difficulty: float = Field(default=0.0, description="Độ khó D (1 đến 10)")
    due: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True, description="Hạn ôn tập tiếp theo")
    reps: int = Field(default=0, description="Số lần lặp lại")
    lapses: int = Field(default=0, description="Số lần quên thẻ (Again)")
    state: str = Field(default="New", description="Trạng thái thẻ (New, Learning, Review, Relearning)")
    last_review: Optional[datetime] = Field(default=None, description="Thời điểm ôn tập gần nhất")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    reviews: List["ReviewLog"] = Relationship(back_populates="card", cascade_delete=True)

class ReviewLog(SQLModel, table=True):
    __tablename__ = "review_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    card_id: uuid.UUID = Field(foreign_key="flashcards.id", index=True)
    rating: int = Field(description="Đánh giá người học: 1: Again, 2: Hard, 3: Good, 4: Easy")
    scheduled_days: float = Field(description="Khoảng cách ngày dự kiến của FSRS")
    elapsed_days: float = Field(description="Số ngày thực tế kể từ lần ôn trước")
    review_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    review_state: str = Field(description="Trạng thái của thẻ tại thời điểm ôn")

    card: Optional[Flashcard] = Relationship(back_populates="reviews")
