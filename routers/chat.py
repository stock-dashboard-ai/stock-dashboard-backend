from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.supervisor import run_supervisor
import utils.db as db

router = APIRouter(tags=["chat"])

VALID_TICKERS = {
    "NVDA", "TSMC", "AAPL", "MSFT", "GOOGL",
    "META", "TSLA", "AMD", "INTC", "AMZN",
    "ASML", "ARM", "QCOM", "AVGO", "AMAT",
}


class ChatRequest(BaseModel):
    ticker: str
    query: str
    session_id: str


@router.post("/chat")
async def chat(req: ChatRequest):
    ticker = req.ticker.upper()
    if ticker not in VALID_TICKERS:
        raise HTTPException(status_code=404, detail=f"{req.ticker} is not a tracked stock")

    history = db.get_chat_history(req.session_id)
    result = await run_supervisor(ticker, req.query, history)

    db.append_chat_turn(req.session_id, ticker, "user", req.query)
    db.append_chat_turn(req.session_id, ticker, "assistant", result["answer"])

    return result
