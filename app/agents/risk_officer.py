# app/agents/risk_officer.py
# Risk Officer Agent — José
#
# Responsibilities:
#   - Consolidate all collected data (RAG + FMP + Fundamental Analysis)
#   - Apply final risk verdict logic
#   - Generate structured Markdown report
#   - Handle both single-company and multi-company comparison mode

from typing import Any


_VERDICT_LABELS = {
    "LOW":      "LOW RISK ✅  (Safe Zone)",
    "MODERATE": "MODERATE RISK ⚠️  (Grey Zone)",
    "HIGH":     "HIGH RISK ❌  (Distress Zone)",
}

_VERDICT_EXPLANATION = {
    "LOW": (
        "Altman Z-Score confirms very low bankruptcy probability. "
        "Conservative leverage and adequate liquidity support financial stability."
    ),
    "MODERATE": (
        "Company shows mixed signals. Z-Score is in the grey zone or leverage is elevated. "
        "Continued monitoring recommended."
    ),
    "HIGH": (
        "Altman Z-Score signals financial distress. "
        "High leverage and/or deteriorating liquidity require immediate attention."
    ),
}


def _company_section(
    ticker:     str,
    fmp:        dict,
    rag:        dict,
    analysis:   dict,
) -> str:
    """Builds the Markdown section for a single company."""
    risk_level  = analysis.get("risk_level", "MODERATE")
    verdict     = _VERDICT_LABELS[risk_level]
    explanation = _VERDICT_EXPLANATION[risk_level]

    z      = fmp.get("altman_z_score") or "N/A"
    growth = fmp.get("revenue_growth")
    growth_pct = f"{round(growth * 100, 1)}%" if growth is not None else "N/A"

    lines = [
        f"### {ticker}  —  {verdict}",
        f"",
        f"**Assessment:** {explanation}",
        f"",
        f"**SEC Filing Context:**",
        f"> {rag.get('texto', 'No context available.')[:600]}",
        f"",
        f"**Source:** {rag.get('fuente', 'N/A')}",
        f"",
        f"| Metric | Value | Source |",
        f"| :--- | :---: | :--- |",
        f"| Stock Price | ${fmp.get('current_price', 'N/A')} | FMP API |",
        f"| P/E Ratio | {fmp.get('pe_ratio', 'N/A')}x | FMP API |",
        f"| Debt / Equity | {fmp.get('debt_to_equity', 'N/A')} | FMP API |",
        f"| Quick Ratio | {fmp.get('quick_ratio', 'N/A')} | FMP API |",
        f"| ROE | {fmp.get('roe', 'N/A')} | FMP API |",
        f"| ROA | {fmp.get('roa', 'N/A')} | FMP API |",
        f"| Gross Margin | {fmp.get('gross_margin', 'N/A')} | FMP API |",
        f"| Revenue Growth YoY | {growth_pct} | FMP API |",
        f"| Altman Z-Score | {z} | Calculated (FMP data) |",
        f"",
        f"**Signal breakdown:**",
    ]

    for signal in analysis.get("signals", []):
        lines.append(f"- {signal}")

    return "\n".join(lines)


def generate_report(
    tickers:    list[str],
    reasoning:  str,
    rag_list:   list[dict],
    fmp_list:   list[dict],
    analyses:   list[dict],
) -> str:
    """
    Generates the final risk assessment report.

    Args:
        tickers:   list of ticker symbols analyzed
        reasoning: supervisor LLM chain-of-thought
        rag_list:  list of RAG results, one per ticker
        fmp_list:  list of FMP results, one per ticker
        analyses:  list of fundamental analysis results, one per ticker

    Returns:
        Formatted Markdown string — the final report
    """
    # Index by ticker for O(1) lookup
    rag_by      = {r["ticker"]: r for r in rag_list}
    fmp_by      = {r["ticker"]: r for r in fmp_list}
    analysis_by = {a["ticker"]: a for a in analyses}

    is_comparison = len(tickers) > 1
    title = (
        f"## 📋 COMPARATIVE RISK ASSESSMENT — {' vs '.join(tickers)}"
        if is_comparison
        else f"## 📋 FINANCIAL RISK ASSESSMENT — {tickers[0]}"
    )

    lines = [
        title,
        "",
        f"**Supervisor Reasoning:** {reasoning}",
        "",
        "---",
        "",
    ]

    for ticker in tickers:
        section = _company_section(
            ticker   = ticker,
            fmp      = fmp_by.get(ticker, {}),
            rag      = rag_by.get(ticker, {}),
            analysis = analysis_by.get(ticker, {"risk_level": "MODERATE", "signals": []}),
        )
        lines.append(section)
        lines.append("\n---\n")

    return "\n".join(lines)
