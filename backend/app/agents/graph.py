import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.agents.evaluator import evaluator_agent
from app.agents.planner import planner_agent

logger = logging.getLogger("agent_graph")

def parse_node(state: AgentState) -> AgentState:
    logger.info(f"LangGraph: Parsing node executed for task {state.task_type}")
    return state

def evaluator_node(state: AgentState) -> AgentState:
    logger.info("LangGraph: Routing to EvaluatorAgent...")
    return evaluator_agent.evaluate(state)

def planner_node(state: AgentState) -> AgentState:
    logger.info("LangGraph: Routing to PlannerAgent...")
    week_num = 2
    if state.input_text:
        import re
        m = re.search(r"\d+", state.input_text)
        if m:
            week_num = int(m.group(0))
    plan = planner_agent.generate_plan(week_number=week_num)
    state.plan_output = plan
    return state

def router_condition(state: AgentState) -> str:
    if state.task_type == "planning":
        return "planner"
    return "evaluator"

# Xây dựng State Graph
workflow = StateGraph(AgentState)

workflow.add_node("parse", parse_node)
workflow.add_node("evaluator", evaluator_node)
workflow.add_node("planner", planner_node)

workflow.add_edge(START, "parse")
workflow.add_conditional_edges(
    "parse",
    router_condition,
    {
        "evaluator": "evaluator",
        "planner": "planner"
    }
)
workflow.add_edge("evaluator", END)
workflow.add_edge("planner", END)

# Compile đồ thị
agent_graph = workflow.compile()
