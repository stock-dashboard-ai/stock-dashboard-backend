from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient

MOCK_PRICE = {
    "dates": ["2025-06-01", "2026-06-01"],
    "closes": [100.0, 120.0],
    "volumes": [1000000, 1200000],
}
MOCK_ANALYST = {"strong_buy": 20, "buy": 10, "hold": 5, "sell": 1, "strong_sell": 0}
MOCK_TARGETS = {"current": 120.0, "low": 100.0, "mean": 130.0, "high": 160.0, "median": 128.0}
MOCK_EARNINGS = {"estimates": [{"period": "0q", "avg": 5.0}]}
MOCK_FINANCIALS = {
    "name": "NVIDIA Corporation", "sector": "Technology",
    "market_cap": 3000000000000, "pe_ratio": 40.0, "forward_pe": 30.0,
    "eps": 10.0, "revenue": 60000000000, "profit_margin": 0.55,
    "dividend_yield": 0.001, "52w_high": 140.0, "52w_low": 80.0,
}
MOCK_NEWS = {"articles": [{"title": "NVDA hits record", "publisher": "Reuters", "date": "2026-06-01", "url": "https://example.com"}]}
MOCK_MDA = {"filing_date": "2026-05-01", "summary": "Revenue grew 80%...", "full_text": "Revenue grew 80% year over year..."}
MOCK_CHAT = {"answer": "NVDA looks strong.", "sources": ["news", "analyst"], "chunks_used": 3}


@pytest.fixture(autouse=True)
def mock_startup(monkeypatch):
    monkeypatch.setattr("data.embeddings.embed_all_tickers", lambda tickers: None)


@pytest.fixture()
def client(mock_startup):
    from main import app
    with TestClient(app) as c:
        yield c


# --- /health ---

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# --- /stock/{ticker}/price ---

@patch("routers.stock.get_price_history", return_value=MOCK_PRICE)
def test_price(mock, client):
    r = client.get("/stock/NVDA/price")
    assert r.status_code == 200
    data = r.json()
    assert "dates" in data and "closes" in data and "volumes" in data
    assert len(data["closes"]) == 2


@patch("routers.stock.get_price_history", return_value=MOCK_PRICE)
def test_price_invalid_ticker(mock, client):
    r = client.get("/stock/FAKE/price")
    assert r.status_code == 404


# --- /stock/{ticker}/analyst ---

@patch("routers.stock.get_analyst_ratings", return_value=MOCK_ANALYST)
def test_analyst(mock, client):
    r = client.get("/stock/NVDA/analyst")
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"strong_buy", "buy", "hold", "sell", "strong_sell"}
    assert data["strong_buy"] == 20


@patch("routers.stock.get_analyst_ratings", return_value=MOCK_ANALYST)
def test_analyst_invalid_ticker(mock, client):
    r = client.get("/stock/FAKE/analyst")
    assert r.status_code == 404


# --- /stock/{ticker}/targets ---

@patch("routers.stock.get_price_targets", return_value=MOCK_TARGETS)
def test_targets(mock, client):
    r = client.get("/stock/NVDA/targets")
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"current", "low", "mean", "high", "median"}
    assert data["current"] == 120.0


@patch("routers.stock.get_price_targets", return_value=MOCK_TARGETS)
def test_targets_invalid_ticker(mock, client):
    r = client.get("/stock/FAKE/targets")
    assert r.status_code == 404


# --- /stock/{ticker}/earnings ---

@patch("routers.stock.get_earnings_estimates", return_value=MOCK_EARNINGS)
def test_earnings(mock, client):
    r = client.get("/stock/NVDA/earnings")
    assert r.status_code == 200
    data = r.json()
    assert "estimates" in data
    assert isinstance(data["estimates"], list)


@patch("routers.stock.get_earnings_estimates", return_value=MOCK_EARNINGS)
def test_earnings_invalid_ticker(mock, client):
    r = client.get("/stock/FAKE/earnings")
    assert r.status_code == 404


# --- /stock/{ticker}/financials ---

@patch("routers.stock.get_financials", return_value=MOCK_FINANCIALS)
def test_financials(mock, client):
    r = client.get("/stock/NVDA/financials")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "NVIDIA Corporation"
    assert data["sector"] == "Technology"
    assert "market_cap" in data and "pe_ratio" in data


@patch("routers.stock.get_financials", return_value=MOCK_FINANCIALS)
def test_financials_invalid_ticker(mock, client):
    r = client.get("/stock/FAKE/financials")
    assert r.status_code == 404


# --- /stock/{ticker}/news ---

@patch("routers.stock.get_news", return_value=MOCK_NEWS)
def test_news(mock, client):
    r = client.get("/stock/NVDA/news")
    assert r.status_code == 200
    data = r.json()
    assert "articles" in data
    assert data["articles"][0]["title"] == "NVDA hits record"


@patch("routers.stock.get_news", return_value=MOCK_NEWS)
def test_news_invalid_ticker(mock, client):
    r = client.get("/stock/FAKE/news")
    assert r.status_code == 404


# --- /stock/{ticker}/mda ---

@patch("routers.stock.get_mda", return_value=MOCK_MDA)
def test_mda(mock, client):
    r = client.get("/stock/NVDA/mda")
    assert r.status_code == 200
    data = r.json()
    assert "filing_date" in data and "summary" in data and "full_text" in data
    assert data["filing_date"] == "2026-05-01"


@patch("routers.stock.get_mda", return_value=MOCK_MDA)
def test_mda_invalid_ticker(mock, client):
    r = client.get("/stock/FAKE/mda")
    assert r.status_code == 404


# --- POST /chat ---

@patch("routers.chat.run_supervisor", new_callable=AsyncMock, return_value=MOCK_CHAT)
@patch("routers.chat.db.append_chat_turn")
@patch("routers.chat.db.get_chat_history", return_value=[])
def test_chat(mock_history, mock_append, mock, client):
    r = client.post("/chat", json={"ticker": "NVDA", "query": "How is NVDA doing?", "session_id": "test-session-1"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and "sources" in data and "chunks_used" in data
    assert data["answer"] == "NVDA looks strong."


@patch("routers.chat.run_supervisor", new_callable=AsyncMock, return_value=MOCK_CHAT)
def test_chat_invalid_ticker(mock, client):
    r = client.post("/chat", json={"ticker": "FAKE", "query": "test", "session_id": "test-session-2"})
    assert r.status_code == 404


@patch("routers.chat.run_supervisor", new_callable=AsyncMock, return_value=MOCK_CHAT)
@patch("routers.chat.db.append_chat_turn")
@patch("routers.chat.db.get_chat_history", return_value=[])
def test_chat_lowercase_ticker(mock_history, mock_append, mock, client):
    r = client.post("/chat", json={"ticker": "nvda", "query": "How is NVDA doing?", "session_id": "test-session-3"})
    assert r.status_code == 200
