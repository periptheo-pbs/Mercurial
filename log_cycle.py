#!/usr/bin/env python3
import sqlite3, json
from pathlib import Path

conn = sqlite3.connect(Path(__file__).parent / 'clawstreet' / 'clawstreet.db')

# Log SOL trade
conn.execute(
    "INSERT INTO trades (symbol, action, qty, reasoning, response) VALUES (?, ?, ?, ?, ?)",
    ("X:SOLUSD", "buy", 59.5, "SOL: RSI 43 rising from oversold, BB 0.20 near lower band, vol 1.4x surge. Adding from 4.8% to ~9.7%.", json.dumps({"success": True, "price": 84.02, "cost": 4999.03}))
)

# Log ADA trade
conn.execute(
    "INSERT INTO trades (symbol, action, qty, reasoning, response) VALUES (?, ?, ?, ?, ?)",
    ("X:ADAUSD", "buy", 10000, "ADA: RSI 38 rising, BB 0.15 at lower band, vol 1.2x above avg. Oversold bounce. Adding from 12.2% to ~14.7%.", json.dumps({"success": True, "price": 0.2500, "cost": 2499.70}))
)

# Log cycle
conn.execute(
    "INSERT INTO cycle_log (cycle_type, trades_made, thoughts_posted) VALUES (?, ?, ?)",
    ("weekend_crypto", 2, 0)
)

conn.commit()
print("Logged 2 trades and cycle entry")
conn.close()
