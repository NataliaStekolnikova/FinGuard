# FinGuard 🛡️
### Multi-Agent Financial Risk Analysis System

> Final project — AI Agents & RAG course · Team: Natalia, Oksana, José

---

## What it does

FinGuard analyzes the financial health of publicly traded companies using SEC EDGAR filings (10-K / 10-Q) and real-time market data from the FMP API, then generates a structured risk assessment report.

```
User: "Analyze Tesla's bankruptcy risk"
              ↓
     Supervisor Agent
     (classifies query, extracts ticker)
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
RAG Retriever       FMP Analyst
(ChromaDB search)   (FMP API call)
    ↓                   ↓
    └─────────┬─────────┘
              ↓
   Fundamental Analyst
   (Altman Z-Score, ratios)
              ↓
       Risk Officer
  (final report + recommendation)
```

---

## Tech Stack

| Component | Tool |
|---|---|
| Agent orchestration | LangGraph |
| Local LLM | qwen3:8b via Ollama |
| Embeddings | nomic-embed-text via Ollama |
| Vector store | ChromaDB (persistent) |
| Real-time financial data | FMP API |
| Historical documents | SEC EDGAR (10-K, 10-Q) |
| API layer | FastAPI |

---

## Project Structure

```
finguard/
├── app/
│   ├── agents/
│   │   └── rag_agent.py        ← RAG retriever (Natalia)
│   ├── graph.py                ← LangGraph orchestration (José)
│   ├── state.py                ← shared agent state
│   └── __init__.py
├── data/
│   └── chroma_db/              ← persistent vector store (git-ignored)
├── docs/                       ← SEC EDGAR HTML filings (git-ignored)
├── indexar.py                  ← document indexing script (Natalia)
├── test_local.py               ← interactive console for testing
├── requirements.txt
├── .env.example                ← environment variable template
└── .gitignore
```

---

## Team

| Member | Role | Responsibilities |
|---|---|---|
| **Natalia** | Data & RAG | SEC EDGAR download, ChromaDB indexing, RAG retriever agent |
| **Oksana** | APIs & Analysis | FMP API integration, FMP analyst agent, Altman Z-Score |
| **José** | Orchestration & Demo | LangGraph supervisor, Risk Officer agent, FastAPI endpoint |

---

## Setup

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running

### 1. Clone the repository

```bash
git clone https://github.com/NataliaStekolnikova/finguard.git
cd finguard
```

### 2. Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your FMP API key
```

### 5. Pull Ollama models

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### 6. Index documents

Place SEC EDGAR HTML/PDF filings inside the `docs/` folder, then run:

```bash
python indexar.py
```

### 7. Run the system

```bash
python test_local.py
```

---

## Data Sources

### FMP API (real-time)
- Stock prices
- Financial ratios (P/E, Debt/Equity, ROE, ROA)
- Income statement, balance sheet, cash flow
- Company news
- Free plan: **250 requests/day** — sufficient for testing

### SEC EDGAR (historical)
- Annual reports 10-K (PDF / HTML)
- Quarterly reports 10-Q
- Indexed in ChromaDB via RAG pipeline
- Fully **free and public**

---

## How RAG works

```
SEC EDGAR HTML/PDF
        ↓
  PyPDFLoader / UnstructuredHTMLLoader
        ↓
  RecursiveCharacterTextSplitter
  (chunk_size=1000, overlap=150)
        ↓
  nomic-embed-text embeddings
        ↓
  ChromaDB (persistent, local)
        ↓
  similarity_search(query, k=4)
        ↓
  Context → LLM (qwen3:8b)
```

---

## Altman Z-Score interpretation

| Z-Score | Zone | Risk |
|---|---|---|
| > 3.0 | Safe zone | Low bankruptcy risk |
| 1.8 – 3.0 | Grey zone | Moderate risk |
| < 1.8 | Distress zone | High bankruptcy risk |

---

## Current status

- [x] LangGraph graph with 5 agents
- [x] ChromaDB indexed with Tesla 10-K / 10-Q
- [x] RAG retriever connected to ChromaDB
- [x] FMP API key configured
- [ ] Real FMP API calls (replacing mock data)
- [ ] Real Altman Z-Score calculation from balance sheet
- [ ] FastAPI endpoint
- [ ] Demo script for presentation

---

## Academic requirements — fulfilled

| Requirement | Implementation |
|---|---|
| Multi-agent system | 5 specialized agents + Supervisor via LangGraph |
| RAG + vector store | SEC filings indexed in ChromaDB with metadata |
| Document indexing | PDF and HTML 10-K/10-Q per company |
| Public API | FMP API with real-time financial data |
| Realistic demo | Real company analysis in seconds |

---

## Environment variables

Copy `.env.example` to `.env` and fill in your values:

```
FMP_API_KEY=your_api_key_here
```

**Never commit `.env` to git.** It is already listed in `.gitignore`.

---

## References

- [Financial Modeling Prep API docs](https://site.financialmodelingprep.com/developer/docs)
- [SEC EDGAR full-text search](https://efts.sec.gov/LATEST/search-index?q=%2210-K%22&dateRange=custom&startdt=2024-01-01&enddt=2025-12-31&forms=10-K)
- [LangGraph documentation](https://langchain-ai.github.io/langgraph/)
- [ChromaDB documentation](https://docs.trychroma.com/)
- [Ollama](https://ollama.com)