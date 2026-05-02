# Mercurial Alpha — ClawStreet Trading Bot

Autonomous trading agent for the ClawStreet paper trading contest. Trades S&P 500 stocks and 14 crypto pairs using multi-factor technical analysis with an invisible planetary timing overlay (PBS).

**Bot Name:** Mercurial Alpha (MERC)
**Bot ID:** `f1fd5a37-67b5-40c1-99a3-5bc10a74fe99`
**Claim URL:** https://www.clawstreet.io/claim/3d6a20ff-ba52-4ae6-bb49-19d73c51eb93
**Verification Code:** `bot-VL44`

---

## Quick Start (Mac Mini)

```bash
# 1. Clone
git clone https://github.com/periptheo-pbs/Mercurial.git
cd Mercurial

# 2. Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example clawstreet/.env
# Edit clawstreet/.env with your ClawStreet API key and Bot ID

# 4. Test vibe check
python3 clawstreet/clawstreet_vibe_check.py

# 5. Run a trading cycle
python3 clawstreet/clawstreet_trader.py
```

---

## Architecture

```
clawstreet_vibe_check.py   → Pure data report (telescope)
       │                     Market status, portfolio, technicals,
       │                     planetary hours, lunar phase
       ▼
Hermes Agent (cronjob)      → Reads report, makes vibe-based decisions
       │
       ▼
clawstreet_trader.py        → Executes trades via ClawStreet API
       │                     Also runs autonomous cycle (scan → score → trade)
       ▼
ClawStreet API              → Paper trading platform
```

The PBS layer is **invisible** — it only influences WHEN the bot checks, never WHAT it says in reasoning text. All public-facing output is purely technical/fundamental.

---

## Files

### Core
| File | Purpose |
|------|---------|
| `clawstreet/clawstreet_trader.py` | **Main bot** — autonomous trading cycle: scan universe, score setups, execute trades, post thoughts |
| `clawstreet/clawstreet_vibe_check.py` | **Vibe check** — pure data collection: market status, portfolio, technicals, planetary hours, lunar phase |
| `clawstreet/exec_trade.py` | **CLI trade executor** — one-off trade via ClawStreet API |

### Utilities
| File | Purpose |
|------|---------|
| `clawstreet/check_balance.py` | Check portfolio balance and position sizing |
| `clawstreet/check_trades.py` | Query recent trades from local SQLite |
| `clawstreet/log_trades.py` | Manually log trades to local SQLite |
| `clawstreet/position_analysis.py` | Position sizing analysis and rebalance calculations |
| `log_cycle.py` | Log cycle entries to local SQLite |

### Shared Engine
| File | Purpose |
|------|---------|
| `engine/planetary_hours.py` | Chaldean planetary hour calculator (shared with Lunalia) |

---

## Strategy

### Scan Universe
**Stocks (30):** AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, AMD, AVGO, CRM, NFLX, JPM, BAC, GS, V, MA, UNH, LLY, ABBV, XOM, CVX, COST, WMT, HD, PLTR, COIN, MSTR, HOOD, SMCI

**Crypto (12):** BTC, ETH, SOL, DOGE, AVAX, ADA, XRP, LINK, UNI, DOT, LTC, ATOM

### Scoring (0-100)
- RSI signal (oversold/overbought) — up to 35 pts
- RSI trend (rising from oversold) — 10 pts
- Volume surge (>1.5x avg) — up to 18 pts
- Price momentum (1d/5d) — up to 18 pts
- Bollinger Band position — up to 15 pts
- Distance from SMA50 — up to 15 pts

### Position Management
- **Max positions:** 10
- **Position sizing:** 4–15% of equity (scaled by conviction × timing quality)
- **Take profit:** +12%
- **Stop loss:** -7%
- **Trailing stop:** -5%

### Timing Layer
Planetary hour quality acts as an invisible filter:
- Jupiter hour: 0.9 (most favorable)
- Mercury hour: 0.8
- Sun/Venus: 0.7
- Moon: 0.6
- Mars: 0.4
- Saturn: 0.3 (scan only, no new entries below 0.35)

---

## Environment Variables

Create `clawstreet/.env`:

| Variable | Description |
|----------|-------------|
| `CLAWSTREET_API_KEY` | API key from ClawStreet platform |
| `CLAWSTREET_BOT_ID` | Bot ID: `f1fd5a37-67b5-40c1-99a3-5bc10a74fe99` |
| `CLAWSTREET_CLAIM_URL` | Claim URL for the bot |
| `CLAWSTREET_VERIFICATION_CODE` | `bot-VL44` |

---

## Cron Job (Hermes Agent)

The bot runs every 30 minutes via Hermes cron:

1. Loads `clawstreet_vibe_check.py` output as context
2. Reviews market conditions, positions, and planetary timing
3. Makes discretionary trading decisions
4. Executes via `clawstreet_trader.py` or direct API calls
5. Posts market thoughts to the ClawStreet feed

---

## Database

Local SQLite at `clawstreet/clawstreet.db`:
- `trades` — executed trades with reasoning
- `thoughts` — posted market thoughts
- `cycle_log` — cycle metadata (trades made, thoughts posted)

This file is gitignored — fresh on clone, built up as the bot runs.

---

## Migration Notes (WSL → Mac Mini)

1. All paths are now relative — no `/home/bakoe/` references
2. `.env` is NOT in git — create from `.env.example`
3. `clawstreet.db` is gitignored — fresh on clone
4. `engine/` is included at repo root (shared dependency)
5. Python 3.10+ required

---

## License

Private — periptheo-pbs
