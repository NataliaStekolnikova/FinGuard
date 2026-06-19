# check_fields.py
# Shows exact field names returned by FMP API

import requests
import json

KEY = "l3WSzJKBhR3HI5j4jk7R9OS9CWsoKj0L"

print("=== RATIOS FIELDS ===")
r = requests.get(
    f"https://financialmodelingprep.com/stable/ratios?symbol=TSLA&limit=1&apikey={KEY}",
    timeout=10
)
data = r.json()
if data:
    for key, value in data[0].items():
        print(f"  {key}: {value}")

print("\n=== KEY METRICS FIELDS ===")
r = requests.get(
    f"https://financialmodelingprep.com/stable/key-metrics?symbol=TSLA&limit=1&apikey={KEY}",
    timeout=10
)
data = r.json()
if data:
    for key, value in data[0].items():
        print(f"  {key}: {value}")
print("\n=== BALANCE SHEET FIELDS ===")
r = requests.get(
    f"https://financialmodelingprep.com/stable/balance-sheet-statement?symbol=TSLA&limit=1&apikey={KEY}",
    timeout=10
)
data = r.json()
if data:
    for key, value in data[0].items():
        print(f"  {key}: {value}")        