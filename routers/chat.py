from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.supervisor import run_supervisor

router = APIRouter(tags=["chat"])

VALID_TICKERS = {
    "NVDA", "TSMC", "AAPL", "MSFT", "GOOGL",
    "META", "TSLA", "AMD", "INTC", "AMZN",
    "ASML", "ARM", "QCOM", "AVGO", "AMAT",
}


class ChatRequest(BaseModel):
    ticker: str
    query: str
    history: list = []


@router.post("/chat")
async def chat(req: ChatRequest):
    ticker = req.ticker.upper()
    if ticker not in VALID_TICKERS:
        raise HTTPException(status_code=404, detail=f"{req.ticker} is not a tracked stock")
    return await run_supervisor(ticker, req.query, req.history)
