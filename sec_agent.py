# sec_agent.py
# Dynamic SEC EDGAR Agent — Natalia
#
# Given a ticker (e.g. "NVDA"), this module:
#   1. Resolves the ticker to its CIK (Central Index Key) in SEC EDGAR
#   2. Checks whether it is already indexed in ChromaDB (cache)
#   3. If not, downloads the latest 10-K and indexes it
#   4. Stores everything in ./data/chroma_db — same location as rag_agent.py
#
# Collection naming convention: {TICKER}-COLLECTION
# This is consistent with rag_agent.py and indexar.py
#
# Usage:
#   from sec_agent import ensure_company_indexed
#   result = ensure_company_indexed("NVDA")
#
# Manual run:
#   python sec_agent.py

import json
import time
from pathlib import Path

import requests
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, BSHTMLLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# SEC EDGAR requires an identifiable User-Agent with a real contact email
HEADERS = {
    "User-Agent": "FinGuard Project nataliastekolnikova2025@gmail.com"
}

DOCS_DIR          = Path("./docs")
CHROMA_DIR        = Path("./data/chroma_db")   # unified with rag_agent.py
TICKER_CACHE_FILE = Path("./sec_tickers_cache.json")

DOCS_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL   = "nomic-embed-text"
OLLAMA_URL    = "http://localhost:11434"
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100

embeddings = OllamaEmbeddings(
    model=EMBED_MODEL,
    base_url=OLLAMA_URL,
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)


# ---------------------------------------------------------------------------
# CHROMADB HELPERS
# ---------------------------------------------------------------------------

def _get_store(ticker: str) -> Chroma:
    """
    Returns the ChromaDB store for a specific ticker.
    Collection: {TICKER}-COLLECTION in ./data/chroma_db
    Consistent with rag_agent.py and indexar.py.
    """
    return Chroma(
        collection_name=f"{ticker.upper()}-COLLECTION",
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )


def _already_indexed(ticker: str) -> bool:
    """Returns True if the ticker collection exists and has documents."""
    try:
        store = _get_store(ticker)
        return store._collection.count() > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# STEP 1 — Resolve ticker → CIK
# ---------------------------------------------------------------------------

def _load_ticker_map() -> dict:
    """
    Downloads (or uses local cache of) the full SEC ticker → CIK map.
    Cache is valid for 24 hours to avoid hitting the SEC API unnecessarily.
    """
    if TICKER_CACHE_FILE.exists():
        age_hours = (time.time() - TICKER_CACHE_FILE.stat().st_mtime) / 3600
        if age_hours < 24:
            return json.loads(TICKER_CACHE_FILE.read_text(encoding="utf-8"))

    print("   [SEC] Downloading ticker → CIK map from SEC EDGAR...")
    url  = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    ticker_map = {
        item["ticker"].upper(): str(item["cik_str"]).zfill(10)
        for item in data.values()
    }

    TICKER_CACHE_FILE.write_text(json.dumps(ticker_map), encoding="utf-8")
    print(f"   [SEC] Ticker map cached ({len(ticker_map)} entries).")
    return ticker_map


def get_cik(ticker: str) -> str | None:
    """Returns the 10-digit CIK for a ticker, or None if not found."""
    return _load_ticker_map().get(ticker.upper())


# ---------------------------------------------------------------------------
# STEP 2 — Find the latest 10-K on EDGAR
# ---------------------------------------------------------------------------

def get_latest_10k_url(cik: str) -> dict | None:
    """
    Finds the most recent 10-K or 10-K/A filing for a given CIK.
    Returns a dict with url, form, filingDate, accessionNumber — or None.
    """
    url  = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    recent = data["filings"]["recent"]

    for i, form in enumerate(recent["form"]):
        if form in ("10-K", "10-K/A"):
            accession_raw    = recent["accessionNumber"][i]
            accession_nodash = accession_raw.replace("-", "")
            primary_doc      = recent["primaryDocument"][i]
            filing_date      = recent["filingDate"][i]

            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{accession_nodash}/{primary_doc}"
            )
            return {
                "url":             doc_url,
                "form":            form,
                "filingDate":      filing_date,
                "accessionNumber": accession_raw,
            }
    return None


# ---------------------------------------------------------------------------
# STEP 3 — Download filing
# ---------------------------------------------------------------------------

def _download_filing(ticker: str, filing_info: dict) -> Path:
    """
    Downloads the filing document and saves it to ./docs/{TICKER}_10K.{ext}
    Returns the local file path.
    """
    print(f"   [SEC] Downloading {filing_info['form']} ({filing_info['filingDate']})...")
    resp = requests.get(filing_info["url"], headers=HEADERS, timeout=60)
    resp.raise_for_status()

    url_lower = filing_info["url"].lower()
    ext       = ".htm" if url_lower.endswith((".htm", ".html")) else ".pdf"
    out_path  = DOCS_DIR / f"{ticker.upper()}_10K{ext}"
    out_path.write_bytes(resp.content)

    print(f"   [SEC] Saved to {out_path} ({out_path.stat().st_size // 1024} KB)")
    return out_path


# ---------------------------------------------------------------------------
# STEP 4 — Index into ChromaDB
# ---------------------------------------------------------------------------

def _index_filing(ticker: str, file_path: Path, filing_info: dict) -> int:
    """
    Loads, splits and indexes a filing into the ticker-specific ChromaDB collection.
    Returns the number of chunks indexed.
    """
    print(f"   [SEC] Indexing {file_path.name} into {ticker.upper()}-COLLECTION...")

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(file_path))
    else:
        loader = BSHTMLLoader(str(file_path), open_encoding="utf-8")

    pages  = loader.load()
    chunks = splitter.split_documents(pages)

    if not chunks:
        print(f"   [SEC] WARNING: No text extracted from {file_path.name}.")
        return 0

    # Enrich each chunk with metadata for filtering and audit
    for chunk in chunks:
        chunk.metadata["ticker"]      = ticker.upper()
        chunk.metadata["source"]      = file_path.name
        chunk.metadata["form"]        = filing_info["form"]
        chunk.metadata["filingDate"]  = filing_info["filingDate"]

    store = _get_store(ticker)
    ids   = [f"{ticker.upper()}_10K_{i}" for i in range(len(chunks))]
    store.add_documents(chunks, ids=ids)

    print(f"   [SEC] Indexed {len(chunks)} chunks into {ticker.upper()}-COLLECTION.")
    return len(chunks)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def ensure_company_indexed(ticker: str, force: bool = False) -> dict:
    """
    Ensures the latest 10-K for `ticker` is indexed in ChromaDB.

    Args:
        ticker: stock symbol, e.g. "NVDA", "TSLA", "AAPL"
        force:  if True, re-downloads and re-indexes even if already cached

    Returns:
        dict with status, chunks_added, filingDate, form, file
    """
    ticker = ticker.upper()

    if not force and _already_indexed(ticker):
        from langchain_chroma import Chroma as _Chroma
        count = _get_store(ticker)._collection.count()
        print(f"   [SEC] {ticker} already indexed ({count} chunks). Using cache.")
        return {
            "ticker":       ticker,
            "status":       "cached",
            "chunks_added": 0,
        }

    cik = get_cik(ticker)
    if cik is None:
        return {
            "ticker":  ticker,
            "status":  "error",
            "message": f"{ticker} not found in SEC EDGAR ticker map.",
        }

    print(f"   [SEC] CIK for {ticker}: {cik}")

    filing_info = get_latest_10k_url(cik)
    if filing_info is None:
        return {
            "ticker":  ticker,
            "status":  "error",
            "message": f"No recent 10-K found for {ticker}.",
        }

    file_path = _download_filing(ticker, filing_info)
    n_chunks  = _index_filing(ticker, file_path, filing_info)

    return {
        "ticker":       ticker,
        "status":       "indexed",
        "chunks_added": n_chunks,
        "filingDate":   filing_info["filingDate"],
        "form":         filing_info["form"],
        "file":         str(file_path),
    }


def query_company(ticker: str, question: str, k: int = 4):
    """
    Searches for relevant fragments for an already-indexed company.
    Consistent interface with rag_agent.py.
    """
    store = _get_store(ticker)
    return store.similarity_search(question, k=k)


# ---------------------------------------------------------------------------
# MANUAL RUN — indexes multiple companies and runs a test query
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("FinGuard — SEC EDGAR Auto-Indexing Agent")
    print("=" * 60)

    companies = ["NVDA", "MSFT", "AMZN", "AAPL"]

    for ticker in companies:
        print(f"\n{'─' * 40}")
        print(f"Processing: {ticker}")
        result = ensure_company_indexed(ticker)
        print(f"Result: {result}")

        if result["status"] in ("cached", "indexed"):
            docs = query_company(ticker, "What are the main risk factors?", k=2)
            print(f"Test query returned {len(docs)} fragments.")
            if docs:
                print(f"Preview: {docs[0].page_content[:200]}...")

    print("\n" + "=" * 60)
    print("All companies processed. Run check_db3.py to verify.")
    print("=" * 60)
