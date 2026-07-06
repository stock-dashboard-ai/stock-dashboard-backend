import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import stock, chat
from routers.schemas import HealthResponse
from data.embeddings import embed_all_tickers
from data.tickers import TRACKED_TICKERS
from utils.db import init_db

load_dotenv()

TAGS_METADATA = [
    {
        "name": "stock",
        "description": "Per-panel dashboard data (price, analyst ratings, targets, earnings, financials, news, MD&A). Each endpoint fetches independently and does not use agents.",
    },
    {
        "name": "chat",
        "description": "Multi-agent chat grounded in dashboard data, powered by a LangGraph supervisor over a Research Agent (live data) and a RAG Agent (Pinecone).",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(asyncio.to_thread(embed_all_tickers, TRACKED_TICKERS))
    yield


app = FastAPI(
    title="Stock Research Dashboard",
    description=(
        "AI-powered stock research dashboard API. Serves per-panel dashboard data for "
        "6 pre-selected stocks (price, analyst ratings, price targets, earnings, "
        "financials, news, MD&A) and a multi-agent chat endpoint grounded in that data."
    ),
    lifespan=lifespan,
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stock.router)
app.include_router(chat.router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Liveness check",
    description="Returns 200 with a static status payload if the server process is up. Does not check Postgres, Pinecone, or WatsonX connectivity.",
)
def health():
    return {"status": "ok"}
