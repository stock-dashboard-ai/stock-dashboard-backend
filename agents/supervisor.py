import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_ibm import ChatWatsonx
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr
from agents.research_agent import run_research
from agents.rag_agent import run_rag

LLAMA4 = "meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
LLAMA3 = "meta-llama/llama-3-3-70b-instruct"


class AgentState(TypedDict):
    ticker: str
    query: str
    history: list
    intent: str
    research_context: str
    rag_context: str
    chunks_used: int
    answer: str
    sources: list[str]


def _get_llm(model_id: str) -> ChatWatsonx:
    return ChatWatsonx(
        model_id=model_id,
        url=SecretStr(os.environ["WATSONX_URL"]),
        apikey=SecretStr(os.environ["WATSONX_API_KEY"]),
        project_id=os.environ["WATSONX_PROJECT_ID"],
    )


def classify_node(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=(
            "Classify what data is needed to answer a stock research question. "
            "Reply with exactly one word: research, rag, or both.\n"
            "- research: live data needed (current price, news, analyst ratings)\n"
            "- rag: static documents needed (MD&A, financials from SEC filings)\n"
            "- both: needs live data AND document context\n"
            "When in doubt, reply: both"
        )),
        HumanMessage(content=state["query"]),
    ]
    try:
        response = _get_llm(LLAMA4).invoke(messages)
    except Exception:
        response = _get_llm(LLAMA3).invoke(messages)

    intent = str(response.content).strip().lower()
    if intent not in ("research", "rag", "both"):
        intent = "both"
    return {"intent": intent}


def _route(state: AgentState) -> list[str]:
    intent = state["intent"]
    if intent == "research":
        return ["research"]
    elif intent == "rag":
        return ["rag"]
    return ["research", "rag"]


def research_node(state: AgentState) -> dict:
    return {
        "research_context": run_research(state["ticker"]),
        "sources": state.get("sources", []) + ["news", "analyst"],
    }


def rag_node(state: AgentState) -> dict:
    context, chunks = run_rag(state["ticker"], state["query"])
    return {
        "rag_context": context,
        "chunks_used": chunks,
        "sources": state.get("sources", []) + ["mda", "financials"],
    }


def synthesize_node(state: AgentState) -> dict:
    parts = []
    if state.get("research_context"):
        parts.append(f"[Live Data]\n{state['research_context']}")
    if state.get("rag_context"):
        parts.append(f"[Document Context]\n{state['rag_context']}")

    messages = [
        SystemMessage(content=(
            f"You are a financial research assistant. Use the provided context about "
            f"{state['ticker']} to answer the user's question accurately and concisely."
        )),
        HumanMessage(content=f"Context:\n\n{chr(10).join(parts)}\n\nQuestion: {state['query']}"),
    ]
    try:
        response = _get_llm(LLAMA4).invoke(messages)
    except Exception:
        response = _get_llm(LLAMA3).invoke(messages)

    return {"answer": str(response.content)}


def _build_graph():
    g = StateGraph(AgentState)
    g.add_node("classify", classify_node)
    g.add_node("research", research_node)
    g.add_node("rag", rag_node)
    g.add_node("synthesize", synthesize_node)

    g.set_entry_point("classify")
    g.add_conditional_edges("classify", _route, ["research", "rag"])
    g.add_edge("research", "synthesize")
    g.add_edge("rag", "synthesize")
    g.add_edge("synthesize", END)

    return g.compile()


_graph = _build_graph()


async def run_supervisor(ticker: str, query: str, history: list) -> dict:
    state: AgentState = {
        "ticker": ticker,
        "query": query,
        "history": history,
        "intent": "both",
        "research_context": "",
        "rag_context": "",
        "chunks_used": 0,
        "answer": "",
        "sources": [],
    }
    result = await _graph.ainvoke(state)
    return {
        "answer": result["answer"],
        "sources": list(set(result.get("sources", []))),
        "chunks_used": result.get("chunks_used", 0),
    }
