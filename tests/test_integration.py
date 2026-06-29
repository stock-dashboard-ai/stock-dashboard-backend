"""
Integration test — requires real API keys in .env.
Run with: pytest tests/test_integration.py -v -s
"""

import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv()

TICKER = "NVDA"

# Skip entire module if required env vars are missing
required_vars = [
    "PINECONE_API_KEY",
    "WATSONX_API_KEY",
    "WATSONX_URL",
    "WATSONX_PROJECT_ID",
]
missing = [v for v in required_vars if not os.environ.get(v)]
if missing:
    pytest.skip(f"Missing env vars: {', '.join(missing)}", allow_module_level=True)


@pytest.fixture(scope="module")
def client():
    # Skip startup embedding — tested separately via embed_ticker unit
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("data.embeddings.embed_all_tickers", lambda tickers: None)
        from main import app

        with TestClient(app) as c:
            yield c


def test_all_endpoints(client):
    # health
    r = client.get("/health")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"

    # price
    r = client.get(f"/stock/{TICKER}/price")
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["dates"]) > 0
    assert len(data["closes"]) == len(data["dates"])
    assert data["closes"][-1] > 0
    print(f"\n  price: latest close ${data['closes'][-1]}")

    # analyst
    r = client.get(f"/stock/{TICKER}/analyst")
    assert r.status_code == 200, r.text
    data = r.json()
    total = sum(data.values())
    assert total > 0, "expected at least one analyst rating"
    print(f"  analyst: {data}")

    # targets
    r = client.get(f"/stock/{TICKER}/targets")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["current"] is not None and data["current"] > 0
    print(f"  targets: current=${data['current']} mean=${data['mean']}")

    # earnings
    r = client.get(f"/stock/{TICKER}/earnings")
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data["estimates"], list)
    print(f"  earnings: {len(data['estimates'])} estimate periods")

    # financials
    r = client.get(f"/stock/{TICKER}/financials")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["name"] is not None
    assert data["sector"] is not None
    print(
        f"  financials: {data['name']} | {data['sector']} | market_cap={data['market_cap']}"
    )

    # news
    r = client.get(f"/stock/{TICKER}/news")
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["articles"]) > 0
    first = data["articles"][0]
    assert first["title"] and first["publisher"]
    print(f"  news: {len(data['articles'])} articles, first: \"{first['title']}\"")

    # mda
    r = client.get(f"/stock/{TICKER}/mda")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["filing_date"] is not None
    assert (
        len(data.get("full_text", "")) > 500
    ), f"MD&A too short: {data.get('full_text', '')[:200]}"
    print(f"  mda: filing_date={data['filing_date']} text_len={len(data['full_text'])}")

    # chat (RAG context may be empty if Pinecone index not yet populated — chat still answers from live data)
    r = client.post(
        "/chat",
        json={
            "ticker": TICKER,
            "query": "What do analysts think about this stock and what does the MD&A say about risks?",
            "history": [],
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["answer"]) > 20, "expected a real LLM answer"
    print(f"  chat sources: {data['sources']}")
    print(f"  chat answer: {data['answer']}")
