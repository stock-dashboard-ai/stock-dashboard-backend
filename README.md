# stock-dashboard-backend

```
stock-dashboard-backend/
├── main.py                  # FastAPI app entry point
├── requirements.txt
├── .env                     # local only, never committed
├── .gitignore
├── agents/
│   ├── __init__.py
│   ├── supervisor.py        # classifies query intent, decides which agents to invoke
│   ├── research_agent.py    # fetches fresh data from yfinance + SEC EDGAR
│   └── rag_agent.py         # Pinecone semantic search and context building
├── data/
│   ├── __init__.py
│   ├── yfinance_client.py   # all yfinance calls; holds in-memory financials dict
│   ├── sec_edgar.py         # SEC EDGAR 10-Q fetching and MD&A parsing
│   └── embeddings.py        # chunking and Pinecone upsert logic
├── routers/
│   ├── __init__.py
│   ├── stock.py             # GET /stock/{ticker} endpoints
│   └── chat.py              # POST /chat endpoint
├── utils/
│   ├── __init__.py
│   ├── db.py                # Render PostgreSQL read/write helpers
│   └── watsonx.py           # WatsonX LLM and embedder setup
```

```mermaid
flowchart TD
    FE["Frontend (Browser)"]

    subgraph API ["FastAPI Backend"]
        STOCK["routers/stock.py\nGET /stock/{ticker}/*"]
        CHAT["routers/chat.py\nPOST /chat"]
    end

    subgraph Agents ["Agent System (chat only)"]
        SUP["Supervisor\nclassify intent"]
        RA["Research Agent\nlive data"]
        RAG["RAG Agent\nstatic docs"]
        SYN["Synthesize\nLLM answer"]
    end

    subgraph DataLayer ["Data Layer"]
        YF["yfinance_client.py"]
        SEC["sec_edgar.py"]
        EMB["embeddings.py"]
    end

    subgraph Storage ["Storage"]
        MEM["In-memory dict\nfinancials cache\n(session only)"]
        PG[("Render PostgreSQL\nmda\nfinancials\nembedded\nchat_history")]
        PC[("Pinecone\nvector index\nnamespace per ticker")]
    end

    subgraph External ["External APIs"]
        YFAPI["yfinance API"]
        EDGARAPI["SEC EDGAR API"]
        WX["WatsonX\nLlama 4 Maverick\n+ embedder"]
    end

    %% Dashboard flow
    FE -->|"parallel panel requests"| STOCK
    STOCK --> YF
    STOCK --> SEC
    YF --> MEM
    MEM -->|miss| PG
    PG -->|miss| YFAPI
    SEC --> PG
    PG -->|miss| EDGARAPI

    %% Chat flow
    FE -->|"session_id + query"| CHAT
    CHAT -->|"load history"| PG
    CHAT --> SUP
    SUP -->|"research"| RA
    SUP -->|"rag"| RAG
    RA --> YF
    RAG --> PC
    PC --> WX
    RA & RAG --> SYN
    SYN -->|"history + context + query"| WX
    WX -->|answer| SYN
    SYN --> CHAT
    CHAT -->|"append turns"| PG
    CHAT -->|answer| FE

    %% Startup embedding (background)
    EMB -.->|"background thread\non startup"| PG
    EMB -.-> WX
    EMB -.-> PC

    %% Styles
    classDef storage fill:#dbeafe,stroke:#3b82f6
    classDef external fill:#fef9c3,stroke:#ca8a04
    classDef agent fill:#f0fdf4,stroke:#16a34a
    class PG,PC,MEM storage
    class YFAPI,EDGARAPI,WX external
    class SUP,RA,RAG,SYN agent
```