#!/usr/bin/env python3
"""Check and close phantom/dust positions."""
import json, requests
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
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Get balance
r = requests.get(f"{BASE_URL}/bots/{BOT_ID}/balance", headers=HEADERS, timeout=15)
balance = r.json()
cash = balance.get("cash", 0)
equity = balance.get("total_equity", 0)
positions = balance.get("positions", [])

print(f"Cash: ${cash:,.2f}")
print(f"Equity: ${equity:,.2f}")
print(f"Return: {balance.get('total_return_pct', 0):+.2f}%")
print(f"\nPositions ({len(positions)}):")
for p in positions:
    sym = p.get("symbol", "?")
    qty = p.get("qty", 0)
    val = p.get("market_value", 0)
    pct = (val / equity * 100) if equity > 0 else 0
    pnl = p.get("unrealized_pl_pct", 0)
    flag = ""
    if pct > 15:
        flag = " *** OVER 15% ***"
    if pct < 0.1:
        flag += " [DUST]"
    print(f"  {sym:15s}: qty={qty:<14} val=${val:>12,.2f} ({pct:5.1f}%) PnL:{pnl:+.1f}%{flag}")
