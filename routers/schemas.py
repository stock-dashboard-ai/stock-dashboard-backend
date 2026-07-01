"""Pydantic response models used to give the Swagger/OpenAPI docs concrete
schemas and field descriptions."""

from pydantic import BaseModel, ConfigDict, Field


class PriceHistory(BaseModel):
    dates: list[str] = Field(
        ..., description="Trading dates, oldest first (YYYY-MM-DD)."
    )
    closes: list[float] = Field(
        ..., description="Closing price for each date, rounded to 2 decimals."
    )
    volumes: list[int] = Field(..., description="Trading volume for each date.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dates": ["2025-06-30", "2025-07-01"],
                "closes": [134.5, 136.2],
                "volumes": [245312000, 198765000],
            }
        }
    )


class AnalystRatings(BaseModel):
    strong_buy: int = Field(
        ..., description="Number of analysts rating the stock 'strong buy'."
    )
    buy: int = Field(..., description="Number of analysts rating the stock 'buy'.")
    hold: int = Field(..., description="Number of analysts rating the stock 'hold'.")
    sell: int = Field(..., description="Number of analysts rating the stock 'sell'.")
    strong_sell: int = Field(
        ..., description="Number of analysts rating the stock 'strong sell'."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "strong_buy": 10,
                "buy": 8,
                "hold": 5,
                "sell": 1,
                "strong_sell": 0,
            }
        }
    )


class PriceTargets(BaseModel):
    current: float | None = Field(None, description="Current market price.")
    low: float | None = Field(None, description="Lowest analyst price target.")
    mean: float | None = Field(None, description="Mean analyst price target.")
    high: float | None = Field(None, description="Highest analyst price target.")
    median: float | None = Field(None, description="Median analyst price target.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current": 800,
                "low": 600,
                "mean": 850,
                "high": 1100,
                "median": 840,
            }
        }
    )


class EPSEstimate(BaseModel):
    period: str | None = Field(
        None,
        description="Estimate period label, e.g. '0q' (current quarter), '+1y' (next year).",
    )
    avg: float | None = Field(None, description="Average analyst EPS estimate.")
    low: float | None = Field(None, description="Lowest analyst EPS estimate.")
    high: float | None = Field(None, description="Highest analyst EPS estimate.")
    yearAgoEps: float | None = Field(
        None, description="Actual EPS for the same period one year ago."
    )
    numberOfAnalysts: int | None = Field(
        None, description="Number of analysts contributing to the estimate."
    )
    growth: float | None = Field(
        None, description="Estimated YoY EPS growth, as a fraction."
    )
    currency: str | None = Field(
        None, description="Currency the EPS figures are denominated in."
    )


class EarningsEstimates(BaseModel):
    estimates: list[EPSEstimate] = Field(
        ..., description="Per-period EPS estimates. Empty list if unavailable."
    )


class FinancialsSnapshot(BaseModel):
    name: str | None = Field(None, description="Company name.")
    sector: str | None = Field(None, description="GICS sector.")
    market_cap: int | None = Field(None, description="Market capitalization in USD.")
    pe_ratio: float | None = Field(
        None, description="Trailing price-to-earnings ratio."
    )
    forward_pe: float | None = Field(
        None, description="Forward price-to-earnings ratio."
    )
    eps: float | None = Field(None, description="Trailing earnings per share.")
    revenue: int | None = Field(
        None, description="Total revenue in USD (most recent fiscal year)."
    )
    profit_margin: float | None = Field(
        None, description="Net profit margin, as a fraction (e.g. 0.55 = 55%)."
    )
    dividend_yield: float | None = Field(
        None, description="Dividend yield, as a fraction."
    )
    field_52w_high: float | None = Field(
        None, alias="52w_high", description="52-week high price."
    )
    field_52w_low: float | None = Field(
        None, alias="52w_low", description="52-week low price."
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "NVIDIA Corporation",
                "sector": "Technology",
                "market_cap": 3200000000000,
                "pe_ratio": 65.2,
                "forward_pe": 45.1,
                "eps": 2.1,
                "revenue": 130000000000,
                "profit_margin": 0.55,
                "dividend_yield": 0.0003,
                "52w_high": 153.13,
                "52w_low": 86.62,
            }
        },
    )


class NewsArticle(BaseModel):
    title: str | None = Field(None, description="Article headline.")
    publisher: str | None = Field(None, description="Publisher / news source name.")
    date: str | None = Field(
        None, description="Publication timestamp as returned by yfinance."
    )
    url: str | None = Field(None, description="Canonical URL of the article.")


class NewsSection(BaseModel):
    articles: list[NewsArticle] = Field(
        ..., description="Recent news articles for the ticker, most recent first."
    )


class MDASummary(BaseModel):
    filing_date: str | None = Field(
        None,
        description="Filing date of the most recent 10-Q (YYYY-MM-DD). Null if no 10-Q is available (e.g. TSMC).",
    )
    preview: str | None = Field(
        None, description="First ~500 characters of the MD&A section."
    )
    full_text: str | None = Field(
        None, description="Full extracted text of the MD&A section."
    )


class ChatResponse(BaseModel):
    answer: str = Field(
        ...,
        description="LLM-generated answer to the user's query, grounded in retrieved and/or live data.",
    )
    sources: list[str] = Field(
        ...,
        description="Which data sources contributed to the answer, e.g. 'news', 'analyst', 'mda', 'financials'.",
    )
    chunks_used: int = Field(
        ...,
        description="Number of Pinecone chunks retrieved by the RAG agent for this answer (0 if the RAG agent was not invoked).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Analysts are broadly positive on NVDA, with 10 strong buy and 8 buy ratings...",
                "sources": ["analyst", "news"],
                "chunks_used": 5,
            }
        }
    )


class HealthResponse(BaseModel):
    status: str = Field(
        ..., description="Liveness indicator. 'ok' when the server is up."
    )
