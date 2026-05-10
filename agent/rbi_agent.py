# agent/rbi_agent.py
# LangGraph agent — decides which tool to call based on the query,
# then synthesizes a final answer from tool outputs.

import sys, logging
from pathlib import Path
from typing import TypedDict, Annotated
import operator

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

sys.path.append(str(Path(__file__).parent.parent))
from config import GROQ_API_KEY, GROQ_MODEL
from agent.tools import ALL_TOOLS

log = logging.getLogger(__name__)


# ── Agent state ───────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]   # accumulate messages
    sources:  list                             # circular metadata for citations


# ── Nodes ─────────────────────────────────────────────────────────────

AGENT_SYSTEM = """You are an expert RBI regulations assistant with access to tools
that search indexed RBI circulars.

TOOLS AVAILABLE:
- vector_search: broad semantic search across all circulars
- department_search: search within a specific RBI department
- circular_summary: retrieve a specific circular by number

RULES:
1. Always use a tool before answering — never answer from memory.
2. Cite circular number, date, and department in your final answer.
3. If the query mentions a specific department, prefer department_search.
4. If the user gives a circular number, use circular_summary.
5. If no relevant circular is found, say so clearly.
"""

def agent_node(state: AgentState) -> AgentState:
    """LLM decides whether to call a tool or give final answer."""
    llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.1)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    messages = [SystemMessage(content=AGENT_SYSTEM)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response], "sources": state.get("sources", [])}

def should_continue(state: AgentState) -> str:
    """Route: if last message has tool_calls → run tools, else → end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

# ── Build graph ────────────────────────────────────────────────────────

def build_agent():
    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")   # after tools → back to agent to synthesize

    return graph.compile()


# ── Public interface ────────────────────────────────────────────────────

_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent

def run_agent(query: str) -> dict:
    """
    Run the RBI agent on a query.
    Returns: {answer: str, sources: list}
    """
    agent = get_agent()
    result = agent.invoke({
        "messages": [HumanMessage(content=query)],
        "sources":  []
    })
    # Extract final text answer from last AIMessage
    final_msg = result["messages"][-1]
    answer    = final_msg.content if hasattr(final_msg, "content") else str(final_msg)
    return {"answer": answer, "sources": result.get("sources", [])}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    r = run_agent("What are the KYC guidelines for banks?")
    print(r["answer"])
