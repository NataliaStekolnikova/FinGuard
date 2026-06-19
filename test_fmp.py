# test_fmp.py
import os

# Set the key directly before importing the agent
os.environ["FMP_API_KEY"] = "l3WSzJKBhR3HI5j4jk7R9OS9CWsoKj0L"

from app.agents.fmp_agent import get_fmp_data

data = get_fmp_data("TSLA")

print("\n=== FMP DATA RECEIVED ===")
for key, value in data.items():
    print(f"{key}: {value}")