#!/usr/bin/env python3
"""Quick position sizing analysis for vibe check."""

equity = 100010.01
cash = 143.01

positions = [
    ("CRM", 100, 184.00, 4.0),
    ("GOOGL", 15, 385.00, 2.1),
    ("PLTR", 44, 144.00, 4.0),
    ("TSLA", 13, 391.00, 3.4),
    ("ADA", 49000, 0.2476, 0.4),
    ("ATOM", 5.7e-13, 1.89, -1.5),
    ("BTC_short", 2.77e-17, 78190, -2.4),
    ("DOT", 32815, 1.20, -0.4),
    ("ETH", 0.25, 2301, 1.6),
    ("XRP", 8800, 1.39, 1.1),
]

print("Position Sizing:")
print("-" * 60)
for sym, qty, price, pnl in positions:
    val = qty * price
    pct = val / equity * 100
    flag = " *** OVER 15% ***" if pct > 15 else ""
    if pct < 0.01:
        flag += " [PHANTOM/DUST]"
    print(f"  {sym:12s}: ${val:>12,.2f}  ({pct:5.1f}%) PnL:{pnl:+.1f}%{flag}")

print(f"  {'Cash':12s}: ${cash:>12,.2f}")
print()

# DOT trim
dot_val = 32815 * 1.20
target_val = equity * 0.15
target_qty = int(target_val / 1.20)
sell_qty = 32815 - target_qty
freed = sell_qty * 1.20
print(f"DOT TRIM NEEDED:")
print(f"  Current: 32,815 DOT = ${dot_val:,.2f} (39.4%)")
print(f"  Target:  {target_qty:,} DOT = ${target_val:,.2f} (15.0%)")
print(f"  SELL:    {sell_qty:,} DOT => frees ${freed:,.2f}")
print()

# CRM trim (stocks - for Monday)
crm_target_qty = int(equity * 0.15 / 184.0)
crm_sell = 100 - crm_target_qty
print(f"CRM TRIM (Monday open):")
print(f"  Current: 100 shares = ${100*184:,.2f} (18.4%)")
print(f"  Target:  {crm_target_qty} shares = ${crm_target_qty*184:,.2f} (15.0%)")
print(f"  SELL:    {crm_sell} shares => frees ${crm_sell*184:,.2f}")
print()

# ETH position sizing after DOT trim
eth_price = 2301
available_after_dot = freed - 500  # keep $500 buffer
eth_add_qty = round(available_after_dot * 0.3 / eth_price, 4)  # 30% to ETH
print(f"ETH ADD POTENTIAL (post-DOT trim):")
print(f"  Available: ~${available_after_dot:,.2f}")
print(f"  30% to ETH: buy {eth_add_qty} ETH @ ${eth_price} = ${eth_add_qty*eth_price:,.2f}")
print()

# SOL analysis
sol_price = 83.71
sol_add_qty = round(available_after_dot * 0.2 / sol_price, 4)
print(f"SOL NEW ENTRY POTENTIAL:")
print(f"  20% to SOL: buy {sol_add_qty} SOL @ ${sol_price} = ${sol_add_qty*sol_price:,.2f}")
