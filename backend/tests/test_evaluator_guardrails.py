from app.agents.state import AgentState
from app.agents.evaluator import evaluator_agent

def test_guardrail_no_official_key():
    """
    KIỂM THỬ NGUYÊN TẮC VÀNG:
    Khi người học chỉ nộp bài mà không có bảng đáp án chính thức,
    Agent TUYỆT ĐỐI KHÔNG ĐƯỢC PHÉP tự đoán đúng/sai hay tính điểm/Band score!
    """
    raw_attempt = """
    3 dentist
    12 a
    24 c
    """
    state = AgentState(
        task_type="evaluation",
        input_text=raw_attempt,
        skill="listening"
    )

    evaluated_state = evaluator_agent.evaluate(state)
    output = evaluated_state.evaluation

    assert evaluated_state.has_official_key is False
    assert output.score_fraction is None
    assert output.band_score is None

    # Xác nhận từng câu đều không bị đánh dấu đúng/sai
    for q in output.questions:
        assert q.is_correct is None
        assert q.correct_answer is None

def test_evaluation_with_official_key():
    """Khi người học cung cấp đáp án đối soát, hệ thống tính toán chính xác"""
    raw_attempt = """
    1 dw137yz - dw307yz / lý do: nghe nhầm w thành 3
    2 31 march - 31 march
    3 dentist - dentist
    """
    state = AgentState(
        task_type="evaluation",
        input_text=raw_attempt,
        skill="listening"
    )

    evaluated_state = evaluator_agent.evaluate(state)
    output = evaluated_state.evaluation

    assert evaluated_state.has_official_key is True
    assert output.score_fraction == "2/3"
    assert output.band_score is not None

    q1 = output.questions[0]
    assert q1.is_correct is False
    assert q1.correct_answer == "dw307yz"

    q2 = output.questions[1]
    assert q2.is_correct is True
