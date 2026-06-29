from data.yfinance_client import get_price_history, get_news, get_analyst_ratings


def run_research(ticker: str) -> str:
    price = get_price_history(ticker)
    news = get_news(ticker)
    analyst = get_analyst_ratings(ticker)

    closes = price.get("closes", [])
    lines = [f"=== {ticker} Live Data ==="]

    if len(closes) >= 2:
        change_pct = ((closes[-1] - closes[0]) / closes[0]) * 100
        lines.append(f"Current Price: ${closes[-1]:.2f}  |  1Y Change: {change_pct:.2f}%")

    lines.append(
        f"Analyst Ratings: Strong Buy={analyst.get('strong_buy', 0)}, "
        f"Buy={analyst.get('buy', 0)}, Hold={analyst.get('hold', 0)}, "
        f"Sell={analyst.get('sell', 0)}, Strong Sell={analyst.get('strong_sell', 0)}"
    )

    articles = news.get("articles", [])[:5]
    if articles:
        lines.append("\nRecent News:")
        for a in articles:
            lines.append(f"- [{a.get('date', '')}] {a.get('title', '')} ({a.get('publisher', '')})")

    return "\n".join(lines)
