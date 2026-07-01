from fastapi import APIRouter, HTTPException, Path
from data.yfinance_client import (
    get_price_history,
    get_analyst_ratings,
    get_price_targets,
    get_earnings_estimates,
    get_financials,
    get_news,
)
from data.sec_edgar import get_mda
from routers.schemas import (
    PriceHistory,
    AnalystRatings,
    PriceTargets,
    EarningsEstimates,
    FinancialsSnapshot,
    NewsSection,
    MDASummary,
)

router = APIRouter(prefix="/stock", tags=["stock"])

VALID_TICKERS = {
    "NVDA",
    "TSMC",
    "AAPL",
    "MSFT",
    "GOOGL",
    "META",
    "TSLA",
    "AMD",
    "INTC",
    "AMZN",
    "ASML",
    "ARM",
    "QCOM",
    "AVGO",
    "AMAT",
}

TickerPath = Path(
    ...,
    description=f"One of the 15 tracked tickers (case-insensitive): {', '.join(sorted(VALID_TICKERS))}.",
    examples=["NVDA"],
)


def _validate(ticker: str) -> str:
    t = ticker.upper()
    if t not in VALID_TICKERS:
        raise HTTPException(status_code=404, detail=f"{ticker} is not a tracked stock")
    return t


@router.get(
    "/{ticker}/price",
    response_model=PriceHistory,
    summary="Get 1-year price history",
    description="Returns daily closing prices and trading volumes for the trailing 1-year period, fetched live from yfinance.",
)
def price(ticker: str = TickerPath):
    return get_price_history(_validate(ticker))


@router.get(
    "/{ticker}/analyst",
    response_model=AnalystRatings,
    summary="Get analyst buy/hold/sell breakdown",
    description="Returns the most recent analyst recommendation counts by rating category, fetched live from yfinance.",
)
def analyst(ticker: str = TickerPath):
    return get_analyst_ratings(_validate(ticker))


@router.get(
    "/{ticker}/targets",
    response_model=PriceTargets,
    summary="Get analyst price targets",
    description="Returns the current price alongside the low/mean/high/median analyst price targets, fetched live from yfinance.",
)
def targets(ticker: str = TickerPath):
    return get_price_targets(_validate(ticker))


@router.get(
    "/{ticker}/earnings",
    response_model=EarningsEstimates,
    summary="Get earnings (EPS) estimates",
    description="Returns per-period analyst EPS estimates, fetched live from yfinance.",
)
def earnings(ticker: str = TickerPath):
    return get_earnings_estimates(_validate(ticker))


@router.get(
    "/{ticker}/financials",
    response_model=FinancialsSnapshot,
    summary="Get financials snapshot",
    description=(
        "Returns a snapshot of key financial metrics (market cap, P/E, EPS, revenue, margins, etc). "
        "Sourced from Postgres if already embedded at startup, otherwise fetched from yfinance and cached."
    ),
)
def financials(ticker: str = TickerPath):
    return get_financials(_validate(ticker))


@router.get(
    "/{ticker}/news",
    response_model=NewsSection,
    summary="Get recent news articles",
    description="Returns recent news articles for the ticker, fetched live from yfinance.",
)
def news(ticker: str = TickerPath):
    return get_news(_validate(ticker))


@router.get(
    "/{ticker}/mda",
    response_model=MDASummary,
    summary="Get latest MD&A from SEC 10-Q",
    description=(
        "Returns the Management's Discussion & Analysis section of the ticker's latest 10-Q filing, "
        "parsed from SEC EDGAR and cached in Postgres. Fields are null for TSMC, which as a foreign "
        "private issuer does not file a 10-Q."
    ),
)
def mda(ticker: str = TickerPath):
    return get_mda(_validate(ticker))
