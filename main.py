from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import stock, chat
from data.embeddings import embed_all_tickers

load_dotenv()

TICKERS = [
    "NVDA", "TSMC", "AAPL", "MSFT", "GOOGL",
    "META", "TSLA", "AMD", "INTC", "AMZN",
    "ASML", "ARM", "QCOM", "AVGO", "AMAT",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    embed_all_tickers(TICKERS)
    yield


app = FastAPI(title="Stock Research Dashboard", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stock.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
