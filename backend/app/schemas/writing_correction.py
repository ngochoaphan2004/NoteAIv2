from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ErrorCategory(str, Enum):
    GRAMMAR = "grammar"                    # Chia thì, hòa hợp chủ vị, mạo từ, đại từ
    COLLOCATION = "collocation"            # Cụm từ học thuật, tự nhiên, từ ngữ chuyên ngành
    PREPOSITION = "preposition"            # Giới từ, cấu trúc câu
    SPELLING = "spelling"                  # Lỗi chính tả, dấu câu
    REDUNDANCY = "redundancy"              # Lặp từ, diễn đạt rườm rà
    COHESION = "cohesion"                  # Liên từ, phép quy chiếu, mạch lạc
    STYLE = "style"                        # Văn phong trang trọng, học thuật

class IELTSCriteria(str, Enum):
    TR_TA = "Task Achievement / Response"
    CC = "Coherence & Cohesion"
    LR = "Lexical Resource"
    GRA = "Grammatical Range & Accuracy"

class InlineEdit(BaseModel):
    original: str = Field(description="Đoạn văn bản/từ gốc có lỗi cần thay thế (phải trùng khớp trong câu)")
    replacement: str = Field(description="Đoạn văn bản/từ chuẩn xác, nâng cấp thay thế vào")
    category: ErrorCategory = Field(default=ErrorCategory.GRAMMAR, description="Nhóm lỗi phân loại")
    criteria: IELTSCriteria = Field(default=IELTSCriteria.GRA, description="Tiêu chí IELTS chịu ảnh hưởng trực tiếp")
    explanation_vi: str = Field(description="Giải thích ngắn gọn lý do sửa bằng Tiếng Việt")

class SentenceCorrection(BaseModel):
    sentence_index: int = Field(description="Số thứ tự câu (1, 2, 3...)")
    original_sentence: str = Field(description="Câu gốc nguyên bản của người học")
    corrected_sentence: str = Field(description="Câu hoàn chỉnh sau khi áp dụng các chỉnh sửa")
    edits: List[InlineEdit] = Field(default_factory=list, description="Danh sách các cụm từ được sửa trong câu")

class WritingCorrectionSchema(BaseModel):
    """Schema cho LLM Structured Output"""
    task_num: int = Field(default=1, description="Task 1 hoặc Task 2")
    sentences: List[SentenceCorrection] = Field(description="Danh sách từng câu với các cụm chỉnh sửa vi mô")
    rubric_feedback: Dict[str, str] = Field(
        default_factory=dict,
        description="Nhận xét chi tiết theo 4 tiêu chí: 'TR_TA', 'CC', 'LR', 'GRA'"
    )
    strengths: List[str] = Field(default_factory=list, description="Điểm mạnh trong bài viết")
    weaknesses: List[str] = Field(default_factory=list, description="Điểm cần cải thiện chính")
    recommended_drills: List[str] = Field(default_factory=list, description="2-3 bài tập micro-session trọng tâm")

class WritingDiffResponse(BaseModel):
    """Output hoàn chỉnh trả về cho API, Quartz & Frontend"""
    task_num: int
    word_count: int
    total_edits: int
    diff_html: str = Field(description="Chuỗi HTML chứa các thẻ huy hiệu 🔴/🟢 trực quan")
    inline_diff_markdown: str = Field(description="Chuỗi Markdown định dạng ~~gạch đỏ~~ -> **xanh**")
    clean_rewritten_text: str = Field(description="Bản bài viết hoàn chỉnh sạch sẽ sau khi sửa")
    sentences: List[SentenceCorrection] = Field(default_factory=list)
    rubric_feedback: Dict[str, str] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommended_drills: List[str] = Field(default_factory=list)
    flashcard_candidates: List[Dict[str, str]] = Field(default_factory=list)
