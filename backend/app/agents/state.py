from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class QuestionResult(BaseModel):
    question_number: int = Field(description="Số thứ tự câu hỏi")
    user_answer: str = Field(description="Đáp án người học đã chọn")
    correct_answer: Optional[str] = Field(default=None, description="Đáp án chuẩn (chỉ ghi nhận khi người học cung cấp)")
    is_correct: Optional[bool] = Field(default=None, description="Đúng / Sai (chỉ đánh giá khi có đáp án chuẩn)")
    trap_type: Optional[str] = Field(default=None, description="Loại bẫy: phát âm -teen/-ty, singular/plural, paraphrase...")
    explanation: Optional[str] = Field(default=None, description="Giải thích chi tiết bẫy âm/ngữ nghĩa")

class EvaluationOutput(BaseModel):
    score_fraction: Optional[str] = Field(default=None, description="Tỷ lệ câu đúng (Ví dụ: '22/40')")
    band_score: Optional[float] = Field(default=None, description="Band score ước lượng chính thức")
    strengths: List[str] = Field(default_factory=list, description="Điểm mạnh trong bài làm")
    weaknesses: List[str] = Field(default_factory=list, description="Các lỗ hổng kiến thức cần khắc phục")
    questions: List[QuestionResult] = Field(default_factory=list, description="Danh sách chi tiết từng câu hỏi")
    recommended_drills: List[str] = Field(default_factory=list, description="Các bài tập micro-session đề xuất (30-35p)")
    feedback: Optional[str] = Field(default=None, description="Nhận xét chi tiết và phân tích sâu từ AI")
    updated_file: Optional[str] = Field(default=None, description="Đường dẫn file Markdown đã được cập nhật bảng đối soát")

class AgentState(BaseModel):
    task_type: str = Field(default="evaluation", description="evaluation | planning | ingestion")
    input_text: str = Field(default="", description="Nội dung đầu vào")
    source_file: Optional[str] = Field(default=None, description="File nguồn")
    skill: str = Field(default="listening", description="listening | reading | writing | speaking")
    has_official_key: bool = Field(default=False, description="Người học đã cung cấp đáp án chính thức chưa")
    evaluation: Optional[EvaluationOutput] = None
    plan_output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
