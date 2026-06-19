# app/agents/rag_agent.py

# Responsibilities:
#   - Connect to local ChromaDB instance
#   - Run semantic similarity search over indexed SEC filings (10-K / 10-Q)
#   - Return structured context per ticker for downstream agents
#
# ChromaDB is populated by running: python indexar.py

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


# Embedding model must match the one used during indexing (indexar.py)
_EMBED_MODEL   = "nomic-embed-text"
_OLLAMA_URL    = "http://localhost:11434"
_CHROMA_PATH   = "./data/chroma_db"
_TOP_K         = 4          # number of fragments to retrieve per query


def _get_store(ticker: str) -> Chroma | None:
    """
    Opens the ChromaDB collection for a given ticker.
    Collection name convention: {TICKER}-COLLECTION (set during indexing).
    Returns None if the collection does not exist or is empty.
    """
    collection_name = f"{ticker.upper()}-COLLECTION"
    try:
        embeddings = OllamaEmbeddings(
            model=_EMBED_MODEL,
            base_url=_OLLAMA_URL,
        )
        store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=_CHROMA_PATH,
        )
        if store._collection.count() == 0:
            return None
        return store
    except Exception as e:
        print(f"   [RAG] ChromaDB connection error for {ticker}: {e}")
        return None


def retrieve(ticker: str, query: str) -> dict:
    """
    Main retrieval function called by the RAG agent node.
    If ChromaDB has no documents for this ticker —
    automatically downloads and indexes the latest 10-K from SEC EDGAR.
    """
    store = _get_store(ticker)

    # Auto-index from SEC EDGAR if not in ChromaDB
    if store is None:
        print(f"   [RAG] {ticker} not in ChromaDB. Fetching from SEC EDGAR...")
        try:
            from sec_agent import ensure_company_indexed
            result = ensure_company_indexed(ticker)
            print(f"   [RAG] SEC EDGAR: {result['status']} — {result.get('chunks_added', 0)} chunks added.")
            store = _get_store(ticker)
        except Exception as e:
            print(f"   [RAG] SEC EDGAR indexing failed: {e}")

    if store is None:
        return {
            "ticker": ticker,
            "texto":  f"No SEC filings available for {ticker}.",
            "fuente": f"ChromaDB — {ticker}-COLLECTION (empty)",
            "found":  False,
        }

    try:
        docs = store.similarity_search(query, k=_TOP_K)
    except Exception as e:
        print(f"   [RAG] Similarity search failed: {e}")
        return {
            "ticker": ticker,
            "texto":  "Search failed.",
            "fuente": f"ChromaDB — {ticker}-COLLECTION (error)",
            "found":  False,
        }

    if not docs:
        return {
            "ticker": ticker,
            "texto":  f"No relevant fragments found for query: '{query}'",
            "fuente": f"ChromaDB — {ticker}-COLLECTION",
            "found":  False,
        }

    fragments = "\n\n---\n\n".join(doc.page_content for doc in docs)
    source    = docs[0].metadata.get("source", f"{ticker}-COLLECTION")

    print(f"   [RAG] Retrieved {len(docs)} fragments from {source}")

    return {
        "ticker": ticker,
        "texto":  fragments,
        "fuente": f"ChromaDB — {source}",
        "found":  True,
    }