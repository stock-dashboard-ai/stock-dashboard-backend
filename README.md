# stock-dashboard-backend

```
stock-dashboard-backend/
├── main.py                  # FastAPI app entry point
├── requirements.txt
├── render.yaml
├── .env                     # local only, never committed
├── .gitignore
├── agents/
│   ├── __init__.py
│   ├── supervisor.py        # routes queries to subagents
│   ├── research_agent.py    # yfinance + SEC data fetching
│   ├── analysis_agent.py    # financial analysis
│   ├── news_agent.py        # news retrieval
│   └── rag_agent.py         # Pinecone retrieval
├── data/
│   ├── __init__.py
│   ├── yfinance_client.py
│   ├── sec_edgar.py
│   └── embeddings.py
├── routers/
│   ├── __init__.py
│   ├── stock.py             # /stock/{ticker} endpoints
│   └── chat.py              # /chat endpoint
├── utils/
│   ├── __init__.py
│   └── cache.py             # JSON file cache
└── cache/                   # cached raw data, gitignored
```
