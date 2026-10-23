from app.agents.state import AgentState
from app.agents.evaluator import evaluator_agent

def test_evaluation_with_cambridge_json_key():
    """
    KIỂM THỬ CHẤM ĐIỂM THEO ĐÁP ÁN CHÍNH THỨC CAMBRIDGE 18 (JSON DATABASE):
    Khi người học nộp bài làm (không cần tự gõ key), hệ thống tự động tra cứu đáp án
    chính thức Cambridge 18 từ JSON database, đối soát chính xác và trích xuất lời giải thích.
    """
    raw_attempt = """
    1 dw137yz
    2 24th April
    3 dentist
    """
    state = AgentState(
        task_type="evaluation",
        input_text=raw_attempt,
        skill="listening",
        source_file="plans/week-01/test-1-listening-p1-p2.md"
    )

    evaluated_state = evaluator_agent.evaluate(state)
    output = evaluated_state.evaluation

    assert evaluated_state.has_official_key is True
    assert output.score_fraction == "2/3"
    assert output.band_score is not None

    # Câu 1 sai: người học điền dw137yz, đáp án chuẩn Cambridge là DW307YZ
    q1 = output.questions[0]
    assert q1.question_number == 1
    assert q1.is_correct is False
    assert q1.correct_answer == "DW307YZ"
    assert "mã bưu chính" in q1.explanation

    # Câu 2 đúng: 24th April khớp với 24(th) April
    q2 = output.questions[1]
    assert q2.question_number == 2
    assert q2.is_correct is True
    assert "24" in q2.correct_answer

    # Câu 3 đúng: dentist
    q3 = output.questions[2]
    assert q3.question_number == 3
    assert q3.is_correct is True
    assert q3.correct_answer == "dentist"

def test_evaluation_with_manual_override_key():
    """Khi người học cung cấp đáp án đối soát thủ công bằng cú pháp tốc ký, hệ thống vẫn hỗ trợ trọn vẹn"""
    raw_attempt = """
    1 dw137yz - dw307yz / lý do: nghe nhầm w thành 3
    2 24th April - 24th April
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

    q2 = output.questions[1]
    assert q2.is_correct is True
