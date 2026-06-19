# test_api.py
import requests

KEY = "l3WSzJKBhR3HI5j4jk7R9OS9CWsoKj0L"

# New FMP API endpoints (post August 2025)
tests = [
    ("Stock quote stable",     f"https://financialmodelingprep.com/stable/quote?symbol=TSLA&apikey={KEY}"),
    ("Profile stable",         f"https://financialmodelingprep.com/stable/profile?symbol=TSLA&apikey={KEY}"),
    ("Ratios stable",          f"https://financialmodelingprep.com/stable/ratios?symbol=TSLA&apikey={KEY}"),
    ("Income stable",          f"https://financialmodelingprep.com/stable/income-statement?symbol=TSLA&apikey={KEY}"),
    ("Key metrics stable",     f"https://financialmodelingprep.com/stable/key-metrics?symbol=TSLA&apikey={KEY}"),
    ("News stable",            f"https://financialmodelingprep.com/stable/news/stock?symbols=TSLA&apikey={KEY}"),
    ("Altman Z stable",        f"https://financialmodelingprep.com/stable/scores?symbol=TSLA&apikey={KEY}"),
]

for name, url in tests:
    r = requests.get(url, timeout=10)
    print(f"{r.status_code} | {name}")
    if r.status_code == 200:
        print(f"         → {r.text[:200]}")
    print()