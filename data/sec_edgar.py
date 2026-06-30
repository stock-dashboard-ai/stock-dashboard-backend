import requests
from bs4 import BeautifulSoup
import utils.db as db

HEADERS = {"User-Agent": "stock-dashboard jinkimcs@gmail.com"}

# CIKs for all 15 tracked stocks (TSMC is a foreign private issuer, no 10-Q)
CIK_MAP = {
    "NVDA": 1045810,
    "AAPL": 320193,
    "MSFT": 789019,
    "GOOGL": 1652044,
    "META": 1326801,
    "TSLA": 1318605,
    "AMD": 2488,
    "INTC": 50863,
    "AMZN": 1018724,
    "ASML": 937556,
    "ARM": 1973239,
    "QCOM": 804328,
    "AVGO": 1730168,
    "AMAT": 796343,
    "TSMC": None,
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


def get_mda(ticker: str) -> dict:
    cached = db.get_mda(ticker)
    if cached:
        return cached

    cik = CIK_MAP.get(ticker)
    if not cik:
        return {"filing_date": None, "preview": None, "full_text": None}

    path, filing_date = _get_latest_10q_path(cik)
    if not path:
        return {"filing_date": None, "preview": None, "full_text": None}

    resp = requests.get(
        f"https://www.sec.gov/Archives/{path}", headers=HEADERS, timeout=15
    )
    resp.raise_for_status()

    text = BeautifulSoup(resp.text, "html.parser").get_text(separator="\n")
    lower = text.lower()

    mda_text = ""
    search_from = 0
    while True:
        start = lower.find("management’s discussion", search_from)
        if start == -1:
            break
        end = lower.find("quantitative and qualitative", start + 1)
        candidate = (
            text[start:end].strip() if end != -1 else text[start : start + 8000].strip()
        )
        if len(candidate) > 500:
            mda_text = candidate
            break
        search_from = start + 1

    if not mda_text:
        mda_text = text[:8000].strip()

    data = {
        "filing_date": filing_date,
        "preview": mda_text[:500],
        "full_text": mda_text,
    }
    db.set_mda(ticker, data["filing_date"], data["preview"], data["full_text"])
    return data
