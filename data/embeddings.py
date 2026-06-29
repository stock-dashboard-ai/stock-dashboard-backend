import os
from datetime import date
import traceback
from pinecone import Pinecone, ServerlessSpec
from data.yfinance_client import get_financials
from data.sec_edgar import get_mda
from utils.cache import get_cache, set_cache
from utils.watsonx import get_embedder

INDEX_NAME = "stock-dashboard"


def _get_index():
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
        pc.create_index(
            name=INDEX_NAME,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(INDEX_NAME)


def _chunk(text: str, size: int = 400, overlap: int = 40) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + size]))
        i += size - overlap
    return chunks


def _upsert(index, embedder, chunks: list[str], meta: dict, namespace: str):
    vectors = []
    for i, chunk in enumerate(chunks):
        vectors.append(
            {
                "id": f"{meta['ticker']}_{meta['source']}_{i}",
                "values": embedder.embed_query(chunk),
                "metadata": {**meta, "text": chunk},
            }
        )
    if vectors:
        index.upsert(vectors=vectors, namespace=namespace)


def embed_ticker(ticker: str) -> None:
    if get_cache(f"embedded_{ticker}"):
        return

    index = _get_index()
    embedder = get_embedder()
    today = date.today().isoformat()

    # Financials
    fin = get_financials(ticker)
    fin_text = " ".join(f"{k}: {v}" for k, v in fin.items() if v is not None)
    _upsert(
        index,
        embedder,
        _chunk(fin_text),
        {
            "ticker": ticker,
            "source": "financials",
            "date": today,
            "document_type": "Financials Summary",
            "title": f"{ticker} Financials",
        },
        namespace=ticker,
    )

    # MD&A
    mda = get_mda(ticker)
    if mda.get("full_text"):
        _upsert(
            index,
            embedder,
            _chunk(mda["full_text"]),
            {
                "ticker": ticker,
                "source": "mda",
                "date": mda.get("filing_date", today),
                "document_type": "10-Q MD&A",
                "title": f"{ticker} 10-Q Management Discussion",
            },
            namespace=ticker,
        )

    set_cache(f"embedded_{ticker}", {"embedded": True})


def embed_all_tickers(tickers: list[str]) -> None:
    for ticker in tickers:
        try:
            embed_ticker(ticker)
        except Exception as e:
            print(f"[embeddings] failed to embed {ticker}")
            print(f"  type: {type(e).__name__}")
            print(f"  error: {str(e)}")
            print(f"  traceback: {traceback.format_exc()}")
