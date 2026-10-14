import logging
from typing import List, Optional, Dict, Any, Type, TypeVar
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger("llm_service")

T = TypeVar("T", bound=BaseModel)

RATE_LIMIT_ERROR_PATTERNS = [
    "429",
    "resource_exhausted",
    "resourceexhausted",
    "quota",
    "rate limit",
    "rate_limit",
    "too many requests",
    "overloaded",
    "temporarily unavailable",
    "capacity",
    "503",
    "unavailable",
    "high demand",
]

def extract_text_content(content: Any) -> str:
    """Trích xuất chuỗi văn bản thuần túy từ phản hồi của LLM (hỗ trợ cả str và list/dict blocks)"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(str(part["text"]))
            elif hasattr(part, "text"):
                text_parts.append(str(part.text))
        return "".join(text_parts)
    return str(content)

def is_rate_limit_error(error: Exception) -> bool:
    """Kiểm tra xem ngoại lệ có phải do quá giới hạn Rate Limit / Quota hay không"""
    err_str = str(error).lower()
    return any(pattern in err_str for pattern in RATE_LIMIT_ERROR_PATTERNS)

class LLMFallbackManager:
    """
    Quản lý danh sách các mô hình LLM với cơ chế Tự Động Chuyển Giao (Failover & Fallback)
    khi gặp Rate Limit (HTTP 429 / ResourceExhausted / Quota Limit / 503 Unavailable).
    """

    def __init__(self):
        self.last_used_model: Optional[str] = None
        self.fallback_history: List[Dict[str, Any]] = []

    def get_models(self) -> List[str]:
        """Lấy danh sách các mô hình theo thứ tự ưu tiên từ cấu hình"""
        return settings.get_model_list()

    def _get_gemini_client(self, model_name: str, temperature: float = 0.2):
        """Khởi tạo ChatGoogleGenerativeAI client cho mô hình chỉ định"""
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY chưa được cấu hình trong backend/.env")

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            max_retries=1,  # Giảm retry nội bộ để failover nhanh sang model tiếp theo
        )

    def generate_text(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Gửi prompt và nhận phản hồi văn bản, tự động chuyển model nếu gặp Rate Limit.
        """
        models = self.get_models()
        errors: List[str] = []

        for idx, model in enumerate(models):
            try:
                logger.info(f"[LLM] Đang thử nghiệm mô hình: {model} ({idx + 1}/{len(models)})")
                
                if settings.LLM_PROVIDER.lower() == "gemini":
                    client = self._get_gemini_client(model)
                    messages = []
                    if system_message:
                        messages.append(("system", system_message))
                    messages.append(("human", prompt))
                    
                    response = client.invoke(messages)
                    self.last_used_model = model
                    logger.info(f"[LLM] Hoàn thành yêu cầu thành công với mô hình: {model}")
                    return extract_text_content(response.content)
                else:
                    # Fallback provider mặc định nếu không phải gemini
                    raise NotImplementedError(f"Provider {settings.LLM_PROVIDER} chưa được hỗ trợ.")

            except Exception as e:
                is_rate_limit = is_rate_limit_error(e)
                error_msg = f"Mô hình '{model}' thất bại: {type(e).__name__} - {e}"
                errors.append(error_msg)

                if is_rate_limit:
                    next_model = models[idx + 1] if idx + 1 < len(models) else "Không còn mô hình dự phòng"
                    logger.warning(
                        f"⚠️ [RATE LIMIT] Mô hình '{model}' đã chạm giới hạn hạn mức (429 / Quota Exceeded). "
                        f"Tự động chuyển giao sang mô hình dự phòng tiếp theo: '{next_model}'..."
                    )
                    self.fallback_history.append({
                        "failed_model": model,
                        "next_model": next_model,
                        "reason": "rate_limit",
                        "error": str(e)
                    })
                else:
                    logger.error(f"[LLM ERROR] {error_msg}")
                    # Nếu gặp lỗi không phải rate limit nhưng vẫn còn model dự phòng, thử tiếp
                    if idx + 1 < len(models):
                        logger.info(f"Đang thử mô hình dự phòng tiếp theo: {models[idx + 1]}...")

        raise RuntimeError(
            f"Tất cả các mô hình trong danh sách ({', '.join(models)}) đều thất bại.\n"
            f"Chi tiết các lỗi:\n" + "\n".join(errors)
        )

    def generate_structured(
        self,
        schema: Type[T],
        prompt: str,
        system_message: Optional[str] = None
    ) -> T:
        """
        Sinh dữ liệu có cấu trúc theo Pydantic schema với cơ chế Multi-Model Fallback.
        """
        models = self.get_models()
        errors: List[str] = []

        for idx, model in enumerate(models):
            try:
                logger.info(f"[LLM Structured] Đang thử nghiệm mô hình: {model} ({idx + 1}/{len(models)})")
                
                if settings.LLM_PROVIDER.lower() == "gemini":
                    client = self._get_gemini_client(model)
                    structured_llm = client.with_structured_output(schema)
                    
                    messages = []
                    if system_message:
                        messages.append(("system", system_message))
                    messages.append(("human", prompt))
                    
                    result = structured_llm.invoke(messages)
                    self.last_used_model = model
                    logger.info(f"[LLM Structured] Thành công với mô hình: {model}")
                    return result
                else:
                    raise NotImplementedError(f"Provider {settings.LLM_PROVIDER} chưa được hỗ trợ.")

            except Exception as e:
                is_rate_limit = is_rate_limit_error(e)
                error_msg = f"Mô hình '{model}' thất bại khi sinh structured output: {e}"
                errors.append(error_msg)

                if is_rate_limit:
                    next_model = models[idx + 1] if idx + 1 < len(models) else "Không còn mô hình dự phòng"
                    logger.warning(
                        f"⚠️ [RATE LIMIT] Mô hình '{model}' chạm giới hạn hạn mức. "
                        f"Chuyển giao sang: '{next_model}'..."
                    )
                    self.fallback_history.append({
                        "failed_model": model,
                        "next_model": next_model,
                        "reason": "rate_limit",
                        "error": str(e)
                    })
                else:
                    logger.error(f"[LLM Structured ERROR] {error_msg}")

        raise RuntimeError(
            f"Không thể sinh dữ liệu cấu trúc qua bất kỳ mô hình nào trong danh sách: {', '.join(models)}.\n"
            f"Lỗi: {errors}"
        )

    def get_status(self) -> Dict[str, Any]:
        """Trả về thông tin trạng thái các mô hình và lịch sử fallback"""
        return {
            "provider": settings.LLM_PROVIDER,
            "configured_models": self.get_models(),
            "last_used_model": self.last_used_model,
            "fallback_events_count": len(self.fallback_history),
            "recent_fallback_events": self.fallback_history[-5:]
        }

llm_service = LLMFallbackManager()
llm_fallback_manager = llm_service

