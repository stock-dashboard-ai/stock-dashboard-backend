import pandas as pd
import yfinance as yf
import utils.db as db

_financials_cache: dict = {}


def _ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(symbol)


def get_price_history(ticker: str) -> dict:
    t = _ticker(ticker)
    hist = t.history(period="1y")
    return {
        "dates": pd.DatetimeIndex(hist.index).strftime("%Y-%m-%d").tolist(),
        "closes": hist["Close"].round(2).tolist(),
        "volumes": hist["Volume"].tolist(),
    }


def get_analyst_ratings(ticker: str) -> dict:
    t = _ticker(ticker)
    recs = t.recommendations
    if not isinstance(recs, pd.DataFrame) or recs.empty:
        return {"strong_buy": 0, "buy": 0, "hold": 0, "sell": 0, "strong_sell": 0}
    latest = recs.tail(1).iloc[0]
    return {
        "strong_buy": int(latest.get("strongBuy", 0)),
        "buy": int(latest.get("buy", 0)),
        "hold": int(latest.get("hold", 0)),
        "sell": int(latest.get("sell", 0)),
        "strong_sell": int(latest.get("strongSell", 0)),
    }


def get_price_targets(ticker: str) -> dict:
    t = _ticker(ticker)
    targets = t.analyst_price_targets
    info = t.info
    return {
        "current": info.get("currentPrice"),
        "low": targets.get("low") if targets else None,
        "mean": targets.get("mean") if targets else None,
        "high": targets.get("high") if targets else None,
        "median": targets.get("median") if targets else None,
    }


def get_earnings_estimates(ticker: str) -> dict:
    t = _ticker(ticker)
    est = t.earnings_estimate
    if est is None or est.empty:
        return {"estimates": []}
    records = est.reset_index().to_dict(orient="records")
    return {"estimates": records}


def get_financials(ticker: str) -> dict:
    if ticker in _financials_cache:
        return _financials_cache[ticker]
    row = db.get_financials(ticker)
    if row:
        _financials_cache[ticker] = row
        return row
    info = _ticker(ticker).info
    data = {
        "name": info.get("longName"),
        "sector": info.get("sector"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "eps": info.get("trailingEps"),
        "revenue": info.get("totalRevenue"),
        "profit_margin": info.get("profitMargins"),
        "dividend_yield": info.get("dividendYield"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
    }
    db.set_financials(ticker, data)
    _financials_cache[ticker] = data
    return data


def get_news(ticker: str) -> dict:
    raw = _ticker(ticker).news or []
    articles = [
        {
            "title": a.get("content", {}).get("title"),
            "publisher": a.get("content", {}).get("provider", {}).get("displayName"),
            "date": a.get("content", {}).get("pubDate"),
            "url": a.get("content", {}).get("canonicalUrl", {}).get("url"),
        }
        for a in raw
    ]
    return {"articles": articles}


def get_info(ticker: str) -> dict:
    return _ticker(ticker).info
