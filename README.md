# FinGuard 🛡️
### Multi-Agent Financial Risk Analysis System

> Final project — AI Agents & RAG course

FinGuard analyzes the financial health of publicly traded companies using real SEC EDGAR filings (10-K / 10-Q) and live market data from the FMP API, then generates a structured risk assessment report.

---

## Project idea

Most financial risk tools require expensive data subscriptions or cloud AI APIs. FinGuard runs **entirely locally** — no cloud LLM, no paid inference. A user types a natural language question about any publicly traded company, and the system:

1. Understands the intent using a local LLM (qwen3:8b)
2. Retrieves context from real SEC filings stored in a local vector database
3. Fetches live financial ratios from the FMP API
4. Calculates the Altman Z-Score (bankruptcy probability model)
5. Generates a structured risk assessment report

---

## How it works

```
User: "Analyze Tesla bankruptcy risk"
              ↓
     Supervisor Agent (qwen3:8b)
     Reasons about query → extracts tickers
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
RAG Retriever       FMP Analyst
ChromaDB search     FMP API calls
SEC 10-K / 10-Q     Price, ratios,
auto-indexed        Altman Z-Score
    ↓                   ↓
    └─────────┬─────────┘
              ↓
   Fundamental Analyst
   Interprets ratios + signals
              ↓
       Risk Officer
  Final report + verdict
```

---

## Agent architecture

| Agent | Role | Tech |
|---|---|---|
| **Supervisor** | Reasons about query using ReAct pattern, extracts tickers, routes to agents | qwen3:8b via Ollama |
| **RAG Retriever** | Searches SEC filings in ChromaDB, auto-indexes new companies on first query | ChromaDB + nomic-embed-text |
| **FMP Analyst** | Fetches real-time price, ratios, calculates Altman Z-Score | FMP API (stable endpoints) |
| **Fundamental Analyst** | Interprets each ratio, generates risk signals | Rule-based |
| **Risk Officer** | Consolidates all data, generates final Markdown report | LangGraph END node |

> **Why LangGraph?** Explicit control over agent routing — each node does exactly one thing, edges define the flow. Transparent, testable, and easy to extend.

> **Why local LLM?** No API costs, no data leaving the machine, works offline after setup.

> **Why RAG?** The LLM alone doesn't know the contents of a company's 10-K filing. RAG retrieves the exact relevant passages from real documents and injects them into the prompt.

---

## Tech stack

| Component | Tool | Why |
|---|---|---|
| Agent orchestration | LangGraph | Explicit graph-based control flow |
| Local LLM | qwen3:8b via Ollama | No cloud, no cost, multilingual |
| Embeddings | nomic-embed-text via Ollama | Local embeddings for RAG |
| Vector store | ChromaDB | Persistent local vector database |
| Real-time data | FMP API (free plan) | Live prices, ratios, financials |
| SEC filings | SEC EDGAR | Free public annual reports (10-K) |
| API layer | FastAPI + Uvicorn | REST API for the multi-agent pipeline |
| UI | Streamlit | Interactive web interface |
| Containerization | Docker + Docker Compose | One-command deployment |

---

## Pre-indexed companies

The following companies are ready to query out of the box:

| Ticker | Company | 10-K Date | Chunks |
|---|---|---|---|
| TSLA | Tesla, Inc. | 2026-04-30 | 261 |
| AAPL | Apple Inc. | 2025-10-31 | 311 |
| NVDA | NVIDIA Corporation | 2026-02-25 | 462 |
| MSFT | Microsoft Corporation | 2025-07-30 | 400 |
| AMZN | Amazon.com, Inc. | 2026-02-06 | 308 |
| META | Meta Platforms, Inc. | 2026-01-29 | 691 |
| GOOGL | Alphabet Inc. | 2026-02-05 | 401 |
| EPAM | EPAM Systems, Inc. | 2026-02-26 | 454 |

Any other publicly traded company on SEC EDGAR is indexed automatically on first query.

---

## 🐳 Setup with Docker (recommended)

The easiest way — everything starts with one command. No Python setup, no Ollama installation needed.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)
- FMP API key from [financialmodelingprep.com/register](https://financialmodelingprep.com/register) (free, 250 requests/day)
- ~10 GB free disk space
- 8 GB RAM minimum (16 GB recommended)

### 1. Clone the repository

```bash
git clone https://github.com/NataliaStekolnikova/FinGuard
cd FinGuard
```

### 2. Create `.env` file

```bash
python -c "open('.env', 'w', encoding='utf-8').write('FMP_API_KEY=your_api_key_here\n')"
```

> ⚠️ Never commit `.env` to git — it's already in `.gitignore`
> ⚠️ Windows users: always create `.env` with Python, not with `echo` — Windows saves files in UTF-16 encoding which Python cannot read

### 3. Start everything

```bash
docker compose up
```

Docker will automatically:
- Start the Ollama LLM server
- Pull `qwen3:8b` (~5.2 GB) and `nomic-embed-text` (~274 MB) models
- Build and start the FastAPI and Streamlit containers
- Start all services in the correct order

> ⏳ **First startup takes 10-15 minutes** — downloading ~5.5 GB of AI models.
> Subsequent startups take only a few seconds (models are cached).

### 4. Open in browser

| Service | URL | Description |
|---|---|---|
| 🖥️ Streamlit UI | http://localhost:8501 | Main web interface |
| 📡 FastAPI docs | http://localhost:8000/docs | REST API + Swagger UI |
| 🤖 Ollama API | http://localhost:11434 | Local LLM server |

### Stop the system

```bash
docker compose down
```

### Rebuild after code changes

```bash
docker compose down
docker compose up --build
```

---

## 💻 Setup without Docker (manual)

### Prerequisites

- Python 3.12
- [Ollama](https://ollama.com) installed and running

### 1. Clone and enter the repository

```bash
git clone https://github.com/NataliaStekolnikova/FinGuard
cd FinGuard
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

### 4. Configure environment

```bash
python -c "open('.env', 'w', encoding='utf-8').write('FMP_API_KEY=your_api_key_here\n')"
```

### 5. Pull Ollama models

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### 6. Start Ollama

```bash
ollama serve
```

### 7. Index SEC filings

```bash
python sec_agent.py
```

Takes 10-15 minutes on first run. Subsequent runs are instant (models cached).

### 8. Run the system

**Console mode:**
```bash
python test_local.py
```

**API mode:**
```bash
python main.py
# Open http://localhost:8000/docs
```

**Streamlit UI:**
```bash
export OLLAMA_HOST=http://localhost:11434   # Linux/Mac
$env:OLLAMA_HOST="http://localhost:11434"   # Windows PowerShell

streamlit run interface_gui.py
# Open http://localhost:8501
```

---

## Example queries

```
Analyze Tesla bankruptcy risk
Compare Tesla and Apple risk
Is Nvidia a safe investment?
Tell me about the iPhone company financial health
Dime cual es el nivel de riesgo de Meta
Compare Microsoft and Amazon risk
```

The Supervisor LLM understands natural language in **any language** and indirect company references:
- "iPhone company" → AAPL
- "Windows company" → MSFT
- "search engine from Google" → GOOGL

---

## Example output

```
## 📋 FINANCIAL RISK ASSESSMENT — TSLA

**Verdict:** LOW RISK ✅ (Safe Zone)
**Assessment:** Altman Z-Score confirms very low bankruptcy probability.

**SEC Filing Context:**
> Tesla 10-K 2026: The company reports stable operating cash flow...
**Source:** ChromaDB — sec_filings | TSLA | 10-K 2026-04-30

| Metric          | Value    | Source              |
| :---            | :---:    | :---                |
| Stock Price     | $375.53  | FMP API             |
| P/E Ratio       | 381.12x  | FMP API             |
| Debt / Equity   | 0.10     | FMP API             |
| Quick Ratio     | 1.77     | FMP API             |
| ROE             | 4.6%     | FMP API             |
| Revenue Growth  | -2.9%    | FMP API             |
| Altman Z-Score  | 17.35    | Calculated (FMP)    |
```

---

## Risks and challenges

| Risk | How we addressed it |
|---|---|
| LLM hallucinations | RAG grounds answers in real SEC documents |
| Slow inference on CPU | qwen3:8b quantized model, acceptable for demo |
| FMP API rate limits | 250 req/day free plan — sufficient for testing |
| Docker healthcheck failing | Replaced `curl` with `ollama list` (curl not in Ollama image) |
| localhost vs container networking | Used `OLLAMA_HOST` env var, `http://ollama:11434` inside Docker |
| `.env` encoding on Windows | Created with Python to ensure UTF-8 encoding |

---

## Data sources

### FMP API (real-time)
- Stock prices, P/E, Debt/Equity, ROE, ROA, Gross Margin
- Income statement, balance sheet, cash flow
- Free plan: **250 requests/day**
- Register at [financialmodelingprep.com](https://financialmodelingprep.com/register)

### SEC EDGAR (historical)
- Annual reports 10-K (auto-downloaded on first query)
- Indexed in ChromaDB — single `sec_filings` collection
- Fully **free and public**

---

## Project structure

```
finguard/
├── Dockerfile                   ← Container build instructions
├── docker-compose.yml           ← Multi-service orchestration
├── .dockerignore                ← Files excluded from Docker build
├── main.py                      ← FastAPI server
├── interface_gui.py             ← Streamlit UI
├── test_local.py                ← Interactive console
├── sec_agent.py                 ← Auto SEC EDGAR indexer
├── app/
│   ├── graph.py                 ← LangGraph topology (nodes + edges only)
│   ├── state.py                 ← Shared agent state (TypedDict)
│   └── agents/
│       ├── supervisor_agent.py  ← ReAct LLM routing
│       ├── rag_agent.py         ← ChromaDB retrieval
│       ├── fmp_agent.py         ← FMP API integration
│       ├── fundamental_agent.py ← Ratio interpretation
│       └── risk_officer.py      ← Report generation
├── data/chroma_db/              ← Vector store (git-ignored)
├── docs/                        ← Downloaded SEC filings (git-ignored)
├── .env.example                 ← Environment template
└── requirements.txt
```

---

## Academic requirements

| Requirement | Implementation |
|---|---|
| Multi-agent system | 5 specialized agents + Supervisor via LangGraph |
| RAG + vector store | SEC filings in ChromaDB `sec_filings` collection |
| Document indexing | 10-K auto-downloaded from SEC EDGAR per company |
| Public API | FMP API with real-time financial data |
| Local LLM | qwen3:8b via Ollama — no cloud dependency |
| Realistic demo | Any public company analyzed in real time |
| Containerization | Full Docker Compose stack — one command deploy |
| Web UI | Streamlit interface |

---

## 👥 Team

| Role | Member | GitHub |
|---|---|---|
| Backend · Docker · SEC Agent | Natalia Stekolnikova | [@NataliaStekolnikova](https://github.com/NataliaStekolnikova) |
| Streamlit UI · LangGraph · Agent orchestration | José Gómez Villasclaras | [@JoseGomezVillasclaras](https://github.com/JoseGomezVillasclaras) |
| FMP API key · Presentation · Integration testing | Oksana Kostyuk | [@Orion-pix](https://github.com/Orion-pix) |

**Supervisor:** [@han057](https://github.com/han057)

---

## Environment variables

```bash
# .env
FMP_API_KEY=your_api_key_here
```

**Never commit `.env` to git.** It is listed in `.gitignore`.

---

## License

MIT
