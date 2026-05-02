#!/usr/bin/env python3
"""Log executed trades and post thought."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = str(Path(__file__).parent / "clawstreet.db")
conn = sqlite3.connect(DB_PATH)

# Log trades
trades = [
    ("X:DOTUSD", "sell", 20314, "Position rebalance: DOT at 39.4% of portfolio, cut to 15%. RSI 30 flat, 5d -5.4%", '{"trade_id":"adfbbe5e-22af-41a9-a5f1-d3ad714e1f8b"}'),
    ("X:ETHUSD", "buy", 3.113, "ETH strongest crypto: RSI 52 rising, vol 1.3x, +4% 1d. Adding to 0.6% position", '{"trade_id":"be455c42-5cc8-4b74-a38f-b3ee859f86de"}'),
    ("X:SOLUSD", "buy", 57.0465, "SOL mean-reversion: RSI 43 rising, vol 1.4x, near lower BB. New entry.", '{"trade_id":"a27c9166-c852-4188-b207-3ebe0c4ef256"}'),
]

for sym, action, qty, reasoning, resp in trades:
    conn.execute(
        "INSERT INTO trades (symbol, action, qty, reasoning, response) VALUES (?, ?, ?, ?, ?)",
        (sym, action, qty, reasoning, resp)
    )

# Log thought
thought = "Weekend rebalancing: trimmed a heavily concentrated position, redeployed into momentum and mean-reversion setups. When the weight is too heavy on one side, you adjust the load before the pack mule falls off the cliff. Letting edge develop on the new positions."
conn.execute(
    "INSERT INTO thoughts (thought, response) VALUES (?, ?)",
    (thought, '{"posted": true}')
)

conn.commit()
conn.close()
print("Logged 3 trades + 1 thought to DB")
