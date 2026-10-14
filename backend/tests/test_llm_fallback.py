import pytest
from unittest.mock import patch, MagicMock
from app.core.config import Settings
from app.services.llm_service import LLMFallbackManager, is_rate_limit_error

def test_model_list_parsing():
    """Kiểm tra việc parse chuỗi danh sách mô hình từ cấu hình"""
    cfg = Settings(
        LLM_MODELS="gemini-1.5-flash, gemini-2.0-flash, gemini-1.5-pro",
        LLM_MODEL="gemini-1.5-flash"
    )
    models = cfg.get_model_list()
    assert models == ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]

def test_single_model_fallback():
    """Khi LLM_MODELS trống, tự động lấy LLM_MODEL đơn lẻ"""
    cfg = Settings(
        LLM_MODELS=None,
        LLM_MODEL="gemini-2.0-flash"
    )
    models = cfg.get_model_list()
    assert models == ["gemini-2.0-flash"]

def test_rate_limit_detection():
    """Kiểm tra nhận diện lỗi Rate Limit / 429 / ResourceExhausted"""
    err_429 = Exception("429 ResourceExhausted: Online quota exceeded for model gemini-1.5-flash")
    assert is_rate_limit_error(err_429) is True

    err_rate_limit = Exception("Rate limit reached for requests per minute")
    assert is_rate_limit_error(err_rate_limit) is True

    err_syntax = ValueError("Invalid prompt syntax")
    assert is_rate_limit_error(err_syntax) is False

def test_fallback_on_rate_limit_success():
    """
    Giả lập:
    - Model 1 (gemini-1.5-flash) bị Rate Limit (429 ResourceExhausted)
    - Hệ thống tự động chuyển sang Model 2 (gemini-2.0-flash) và thực thi thành công
    """
    manager = LLMFallbackManager()

    mock_client_fail = MagicMock()
    mock_client_fail.invoke.side_effect = Exception("429 ResourceExhausted: Quota exceeded")

    mock_client_success = MagicMock()
    mock_client_success.invoke.return_value = MagicMock(content="Phản hồi từ mô hình dự phòng gemini-2.0-flash")

    def mock_get_client(model_name: str, **kwargs):
        if model_name == "gemini-1.5-flash":
            return mock_client_fail
        return mock_client_success

    with patch.object(manager, "get_models", return_value=["gemini-1.5-flash", "gemini-2.0-flash"]), \
         patch.object(manager, "_get_gemini_client", side_effect=mock_get_client):

        result = manager.generate_text("Prompt kiểm tra")

        assert result == "Phản hồi từ mô hình dự phòng gemini-2.0-flash"
        assert manager.last_used_model == "gemini-2.0-flash"
        assert len(manager.fallback_history) == 1
        assert manager.fallback_history[0]["failed_model"] == "gemini-1.5-flash"
        assert manager.fallback_history[0]["next_model"] == "gemini-2.0-flash"
        assert manager.fallback_history[0]["reason"] == "rate_limit"

def test_all_models_rate_limited():
    """Khi tất cả mô hình trong danh sách đều bị Rate Limit, ném ra RuntimeError có giải thích"""
    manager = LLMFallbackManager()

    mock_client = MagicMock()
    mock_client.invoke.side_effect = Exception("429 ResourceExhausted: Quota exceeded")

    with patch.object(manager, "get_models", return_value=["gemini-1.5-flash", "gemini-2.0-flash"]), \
         patch.object(manager, "_get_gemini_client", return_value=mock_client):

        with pytest.raises(RuntimeError) as exc_info:
            manager.generate_text("Prompt kiểm tra")

        assert "Tất cả các mô hình trong danh sách" in str(exc_info.value)

