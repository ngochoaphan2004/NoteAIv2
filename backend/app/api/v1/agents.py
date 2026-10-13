from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from app.agents.state import AgentState, EvaluationOutput
from app.agents.graph import agent_graph

router = APIRouter(prefix="/agents", tags=["Autonomous Agents"])

class EvaluateRequest(BaseModel):
    attempt_text: str = Field(..., description="Văn bản bài làm hoặc cú pháp shorthand của người học")
    skill: str = Field(default="listening", description="listening | reading | writing | speaking")
    source_file: Optional[str] = Field(default=None)

class PlanRequest(BaseModel):
    week_number: int = Field(default=2, ge=1, le=52)

@router.post("/evaluate", response_model=EvaluationOutput)
def evaluate_test_attempt(req: EvaluateRequest):
    """
    Gửi bài test để đối soát.
    TUÂN THỦ NGUYÊN TẮC VÀNG: Không suy đoán điểm/đáp án nếu người học chưa cung cấp key.
    """
    initial_state = AgentState(
        task_type="evaluation",
        input_text=req.attempt_text,
        skill=req.skill,
        source_file=req.source_file
    )

    final_state = agent_graph.invoke(initial_state)

    if final_state.get("error"):
        raise HTTPException(status_code=400, detail=final_state["error"])

    eval_result = final_state.get("evaluation")
    if not eval_result:
        raise HTTPException(status_code=500, detail="Không nhận được kết quả đánh giá từ Agent.")

    return eval_result

@router.post("/plan")
def generate_adaptive_plan(req: PlanRequest):
    """Tự động sinh lịch học Micro-sessions 30-35p thích ứng cho tuần học"""
    initial_state = AgentState(
        task_type="planning",
        input_text=f"Tuần {req.week_number}"
    )

    final_state = agent_graph.invoke(initial_state)
    return final_state.get("plan_output", {})
