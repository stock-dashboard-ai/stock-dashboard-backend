import re
import requests
from bs4 import BeautifulSoup
import utils.db as db
from utils.watsonx import get_llm

HEADERS = {"User-Agent": "stock-dashboard jinkimcs@gmail.com"}

MDA_ANCHOR = re.compile(r"item\s*2\.\s*management's discussion")

# CIKs for all 6 tracked stocks.
# Replace later with dynamic lookup from "https://www.sec.gov/files/company_tickers.json"
CIK_MAP = {
    "NVDA": 1045810,
    "AAPL": 320193,
    "MSFT": 789019,
    "GOOGL": 1652044,
    "META": 1326801,
    "TSLA": 1318605,
}


def _get_latest_10q_path(cik: int) -> tuple[str | None, str | None]:
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    filings = resp.json().get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    dates = filings.get("filingDate", [])
    accessions = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])
    for i, form in enumerate(forms):
        if form == "10-Q":
            accession = accessions[i].replace("-", "")
            return f"edgar/data/{cik}/{accession}/{primary_docs[i]}", dates[i]
    return None, None


def _summarize_mda(ticker: str, text: str) -> str:
    prompt = (
        f"Summarize the following Management's Discussion and Analysis (MD&A) "
        f"section from {ticker}'s latest 10-Q filing in 3-4 sentences for a stock "
        f"research dashboard. Focus on revenue, margins, and notable risks or "
        f"trends. Do not add information not present in the text. Output only "
        f"the summary itself, with no preamble, introduction, or lead-in phrase. "
        f"Write the summary in Korean."
        f"\n\nMD&A Full Text:\n{text}"
    )
    response = get_llm().invoke(prompt)
    content = response.content
    return content.strip() if isinstance(content, str) else str(content).strip()


def get_mda(ticker: str) -> dict:
    cached = db.get_mda(ticker)
    if cached:
        return cached

    cik = CIK_MAP.get(ticker)
    if not cik:
        return {"filing_date": None, "summary": None, "full_text": None}

    path, filing_date = _get_latest_10q_path(cik)
    if not path:
        return {"filing_date": None, "summary": None, "full_text": None}

    resp = requests.get(
        f"https://www.sec.gov/Archives/{path}", headers=HEADERS, timeout=15
    )
    resp.raise_for_status()

    text = BeautifulSoup(resp.text, "html.parser").get_text(separator="\n")
    lower = text.lower().replace("\xa0", " ").replace("’", "'")

    mda_text = ""
    for m in MDA_ANCHOR.finditer(lower):
        start = m.start()
        end = lower.find("item 3.", start + 1)
        candidate = (
            text[start:end].strip() if end != -1 else text[start : start + 8000].strip()
        )
        if len(candidate) > 2000:
            mda_text = candidate
            break

    if not mda_text:
        mda_text = text[:8000].strip()

    try:
        summary = _summarize_mda(ticker, mda_text)
    except Exception:
        summary = mda_text[:500]

    data = {
        "filing_date": filing_date,
        "summary": summary,
        "full_text": mda_text,
    }
    db.set_mda(ticker, data["filing_date"], data["summary"], data["full_text"])
    return data
