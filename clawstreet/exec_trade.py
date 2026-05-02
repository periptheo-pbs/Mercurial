#!/usr/bin/env python3
"""Execute trade via ClawStreet API."""
import json, requests, sys, os
from pathlib import Path

env_path = Path(__file__).parent / ".env"
env = {}
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

API_KEY = env.get("CLAWSTREET_API_KEY", "")
BOT_ID = env.get("CLAWSTREET_BOT_ID", "")
BASE_URL = "https://www.clawstreet.io/api"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

trade = {
    "symbol": sys.argv[1],
    "action": sys.argv[2],
    "qty": float(sys.argv[3]),
    "reasoning": sys.argv[4] if len(sys.argv) > 4 else "Technical setup"
}

print(f"Executing: {trade['action'].upper()} {trade['qty']} {trade['symbol']}")
print(f"Reasoning: {trade['reasoning']}")

url = f"{BASE_URL}/bots/{BOT_ID}/trades"
r = requests.post(url, headers=HEADERS, json=trade, timeout=15)
print(f"Status: {r.status_code}")
try:
    result = r.json()
    print(f"Response: {json.dumps(result, indent=2)}")
except:
    print(f"Raw: {r.text[:500]}")
