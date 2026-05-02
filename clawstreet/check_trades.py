#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('clawstreet/clawstreet.db')
rows = conn.execute('SELECT symbol, action, qty, ts FROM trades ORDER BY ts DESC LIMIT 10').fetchall()
for r in rows:
    print(f'{r[3]} | {r[1]:5s} | {r[0]:10s} | qty={r[2]}')
if not rows:
    print("No trades found")
conn.close()
