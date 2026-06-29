from fastapi import APIRouter, HTTPException
from data.yfinance_client import (
    get_price_history,
    get_analyst_ratings,
    get_price_targets,
    get_earnings_estimates,
    get_financials,
    get_news,
)
from data.sec_edgar import get_mda

router = APIRouter(prefix="/stock", tags=["stock"])

VALID_TICKERS = {
    "NVDA", "TSMC", "AAPL", "MSFT", "GOOGL",
    "META", "TSLA", "AMD", "INTC", "AMZN",
    "ASML", "ARM", "QCOM", "AVGO", "AMAT",
}


def _validate(ticker: str) -> str:
    t = ticker.upper()
    if t not in VALID_TICKERS:
        raise HTTPException(status_code=404, detail=f"{ticker} is not a tracked stock")
    return t


@router.get("/{ticker}/price")
def price(ticker: str):
    return get_price_history(_validate(ticker))


@router.get("/{ticker}/analyst")
def analyst(ticker: str):
    return get_analyst_ratings(_validate(ticker))


@router.get("/{ticker}/targets")
def targets(ticker: str):
    return get_price_targets(_validate(ticker))


@router.get("/{ticker}/earnings")
def earnings(ticker: str):
    return get_earnings_estimates(_validate(ticker))


@router.get("/{ticker}/financials")
def financials(ticker: str):
    return get_financials(_validate(ticker))


@router.get("/{ticker}/news")
def news(ticker: str):
    return get_news(_validate(ticker))


@router.get("/{ticker}/mda")
def mda(ticker: str):
    return get_mda(_validate(ticker))
