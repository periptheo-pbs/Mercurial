#!/usr/bin/env python3
"""
ClawStreet Vibe Check — Pure Data Collection
=============================================
Telescope for the Mercurial Alpha bot. Collects market data, technicals,
planetary hours, and portfolio state. Makes NO trading decisions.

Output is fed to Hermes via cronjob for vibes-based discretionary decisions.
"""

import os
import sys
import json
import time
import datetime
from pathlib import Path

import requests
import pytz

# ─── Path Setup ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent  # pbs-vibes/
sys.path.insert(0, str(PROJECT_ROOT))

from engine.planetary_hours import (
    get_planetary_hour_at_time,
    get_active_kill_zone,
    KILL_ZONES,
    KZ_TO_LOCATION,
    DAY_RULERS,
    LOCATIONS,
)

# ─── Configuration ───────────────────────────────────────────────────────────
ENV_PATH = SCRIPT_DIR / ".env"
BASE_URL = "https://www.clawstreet.io/api"

# Scan universe — top liquid names
SCAN_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    "AMD", "AVGO", "CRM", "NFLX",
    "JPM", "BAC", "GS", "V", "MA",
    "UNH", "LLY", "ABBV",
    "XOM", "CVX",
    "COST", "WMT", "HD",
    "PLTR", "COIN", "MSTR", "HOOD", "SMCI",
]

SCAN_CRYPTO = [
    "X:BTCUSD", "X:ETHUSD", "X:SOLUSD", "X:DOGEUSD",
    "X:AVAXUSD", "X:ADAUSD", "X:XRPUSD", "X:LINKUSD",
    "X:UNIUSD", "X:DOTUSD", "X:LTCUSD", "X:ATOMUSD",
]


def load_env():
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = load_env()
API_KEY = ENV.get("CLAWSTREET_API_KEY", "")
BOT_ID = ENV.get("CLAWSTREET_BOT_ID", "")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


# ─── API Helpers ─────────────────────────────────────────────────────────────

def api_get(path, auth=True, retries=3):
    headers = HEADERS if auth else {}
    url = f"{BASE_URL}{path}"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 429:
                wait = min(2 ** attempt * 2, 10)
                print(f"  [RATE] 429, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            if r.status_code == 401:
                return None
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(1)
    return None


def get_market_status():
    data = api_get("/market-status", auth=False)
    if data:
        return data.get("isOpen", False), data
    return False, {}


def get_balance():
    data = api_get(f"/bots/{BOT_ID}/balance")
    return data or {}


def get_quotes(symbols):
    """Get current quotes. Batch up to 20."""
    if not symbols:
        return {}
    all_quotes = {}
    for i in range(0, len(symbols), 20):
        batch = symbols[i:i + 20]
        sym_str = ",".join(batch)
        data = api_get(f"/data/quotes?symbols={sym_str}", auth=False)
        if data and "quotes" in data:
            all_quotes.update(data["quotes"])
        time.sleep(0.2)
    return all_quotes


def get_history_batch(symbols, periods=20):
    """Batch history fetch — up to 10 symbols per request."""
    if not symbols:
        return {}
    results = {}
    for i in range(0, len(symbols), 10):
        batch = symbols[i:i + 10]
        sym_str = ",".join(batch)
        data = api_get(f"/data/history?symbols={sym_str}&periods={periods}")
        if data:
            results.update({s: data.get(s, {}) for s in batch if s in data})
        time.sleep(0.5)
    return results


def get_market_context():
    data = api_get("/data/market", auth=False)
    return data or {}


def get_sentiment(symbol):
    data = api_get(f"/data/sentiment?symbol={symbol}", auth=False)
    return data or {}


def get_thought_context():
    data = api_get(f"/bots/{BOT_ID}/thought-context")
    return data or {}


# ─── Lunar Phase (Pure Math) ─────────────────────────────────────────────────

REF_NEW_MOON_JD = 2451550.39  # Calibrated to May 2, 2026 Full Moon
SYNODIC_MONTH = 29.530588853


def get_lunar_phase(dt_utc=None):
    """Calculate current lunar phase. Returns (fraction, phase_name, emoji)."""
    if dt_utc is None:
        dt_utc = datetime.datetime.now(pytz.UTC)
    # Julian Day
    a = (14 - dt_utc.month) // 12
    y = dt_utc.year + 4800 - a
    m = dt_utc.month + 12 * a - 3
    jd = dt_utc.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd += (dt_utc.hour - 12) / 24.0 + dt_utc.minute / 1440.0 + dt_utc.second / 86400.0

    days_since_ref = jd - REF_NEW_MOON_JD
    frac = (days_since_ref % SYNODIC_MONTH) / SYNODIC_MONTH

    if frac < 0.0625:
        name, emoji = "New Moon", "🌑"
    elif frac < 0.1875:
        name, emoji = "Waxing Crescent", "🌒"
    elif frac < 0.3125:
        name, emoji = "First Quarter", "🌓"
    elif frac < 0.4375:
        name, emoji = "Waxing Gibbous", "🌔"
    elif frac < 0.5625:
        name, emoji = "Full Moon", "🌕"
    elif frac < 0.6875:
        name, emoji = "Waning Gibbous", "🌖"
    elif frac < 0.8125:
        name, emoji = "Last Quarter", "🌗"
    elif frac < 0.9375:
        name, emoji = "Waning Crescent", "🌘"
    else:
        name, emoji = "New Moon", "🌑"

    return frac, name, emoji


def get_next_full_moon(dt_utc=None):
    """Estimate next Full Moon date."""
    if dt_utc is None:
        dt_utc = datetime.datetime.now(pytz.UTC)
    frac = get_lunar_phase(dt_utc)[0]
    # Full moon is at frac ~0.5
    if frac < 0.5:
        days_to_fm = (0.5 - frac) * SYNODIC_MONTH
    else:
        days_to_fm = (1.5 - frac) * SYNODIC_MONTH
    fm_date = dt_utc + datetime.timedelta(days=days_to_fm)
    return fm_date, days_to_fm


# ─── Planetary Context ───────────────────────────────────────────────────────

def get_esoteric_context():
    """Build the full esoteric picture for the current moment."""
    now_utc = datetime.datetime.now(pytz.UTC)
    day_ruler = DAY_RULERS[now_utc.weekday()]

    # Active KZ
    active_kz = get_active_kill_zone(now_utc)
    active_kz_label = KILL_ZONES[active_kz]["label"] if active_kz else "None (outside KZ)"

    # Planetary hours for each KZ location
    kz_hours = {}
    for kz_name in KILL_ZONES:
        loc_key = KZ_TO_LOCATION[kz_name]
        ph = get_planetary_hour_at_time(loc_key, now_utc)
        if ph:
            progress = 0
            total_secs = (ph["end_utc"] - ph["start_utc"]).total_seconds()
            elapsed = (now_utc - ph["start_utc"]).total_seconds()
            if total_secs > 0:
                progress = elapsed / total_secs * 100
            kz_hours[kz_name] = {
                "planet": ph["planet"],
                "hour_number": ph["hour_number"],
                "is_day": ph["is_day_hour"],
                "progress_pct": progress,
                "start_utc": ph["start_utc"].strftime("%H:%M"),
                "end_utc": ph["end_utc"].strftime("%H:%M"),
                "duration_min": total_secs / 60,
            }

    # Lunar phase
    lunar_frac, lunar_name, lunar_emoji = get_lunar_phase(now_utc)
    fm_date, days_to_fm = get_next_full_moon(now_utc)

    return {
        "timestamp_utc": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "day_ruler": day_ruler,
        "active_kz": active_kz,
        "active_kz_label": active_kz_label,
        "kz_hours": kz_hours,
        "lunar_frac": lunar_frac,
        "lunar_name": lunar_name,
        "lunar_emoji": lunar_emoji,
        "full_moon_date": fm_date.strftime("%Y-%m-%d %H:%M UTC"),
        "days_to_full_moon": round(days_to_fm, 1),
    }


# ─── Report Builder ──────────────────────────────────────────────────────────

def fmt_price(p):
    """Format price — avoid rounding sub-$1 coins to $0."""
    if p is None or p == 0:
        return "—"
    if abs(p) < 1:
        return f"${p:.4f}"
    if abs(p) < 100:
        return f"${p:.2f}"
    return f"${p:,.0f}"


def build_report():
    """Build the full vibe check report."""
    lines = []
    sep = "─" * 60

    # ── Header ──
    eso = get_esoteric_context()
    lines.append(f"════════════════════════════════════════════════════════════")
    lines.append(f"  MERCURIAL ALPHA — ClawStreet Vibe Check")
    lines.append(f"  {eso['timestamp_utc']}  |  Day Ruler: {eso['day_ruler']}")
    lines.append(f"════════════════════════════════════════════════════════════")
    lines.append("")

    # ── Market Status ──
    market_open, market_data = get_market_status()
    lines.append(f"{'── Market Status ':-<60}")
    lines.append(f"  Status:    {'OPEN' if market_open else 'CLOSED'}")
    if market_data.get("nextOpen"):
        lines.append(f"  Next Open: {market_data['nextOpen']}")
    if market_data.get("nextClose"):
        lines.append(f"  Next Close: {market_data['nextClose']}")
    lines.append("")

    # ── Portfolio ──
    balance = get_balance()
    if not balance or (isinstance(balance.get("error"), dict)):
        err = balance.get("error", {})
        if isinstance(err, dict) and err.get("code") == "BOT_NOT_CLAIMED":
            lines.append("  [FATAL] Bot not claimed! Visit claim URL.")
        else:
            lines.append(f"  [ERROR] Balance: {balance}")
        return "\n".join(lines)

    cash = balance.get("cash", 0)
    total_equity = balance.get("total_equity", 0)
    total_return = balance.get("total_return_pct", 0)
    positions = balance.get("positions", [])

    lines.append(f"{'── Portfolio ':-<60}")
    lines.append(f"  Cash:      ${cash:,.2f}")
    lines.append(f"  Equity:    ${total_equity:,.2f}")
    lines.append(f"  Return:    {total_return:+.2f}%")
    lines.append(f"  Positions: {len(positions)}")
    lines.append("")

    if positions:
        lines.append(f"{'── Open Positions ':-<60}")
        for p in positions:
            sym = p.get("symbol", "?")
            qty = p.get("qty", 0)
            avg = p.get("avg_cost", 0)
            cur = p.get("current_price", 0)
            up = p.get("unrealized_pl_pct", 0)
            side = p.get("side", "long")
            lines.append(f"  {sym}: {qty} @ {fmt_price(avg)} → {fmt_price(cur)} ({up:+.1f}%) [{side}]")
        lines.append("")

    # ── Esoteric Context ──
    lines.append(f"{'── Planetary Hours (Active KZ Highlighted) ':-<60}")
    lines.append(f"  Active KZ: {eso['active_kz_label']}")
    lines.append("")
    for kz_name, kz in KILL_ZONES.items():
        h = eso["kz_hours"].get(kz_name)
        if not h:
            continue
        marker = " ◀️" if kz_name == eso["active_kz"] else ""
        day_night = "☀️" if h["is_day"] else "🌙"
        lines.append(f"  {kz['label']:20s}  {h['planet']:8s}  Hour {h['hour_number']:2d}  {day_night}  {h['start_utc']}-{h['end_utc']} UTC  {h['duration_min']:.0f}min  {h['progress_pct']:.0f}%{marker}")
    lines.append("")

    lines.append(f"{'── Lunar Phase ':-<60}")
    lines.append(f"  Phase:     {eso['lunar_emoji']} {eso['lunar_name']} ({eso['lunar_frac']*100:.1f}%)")
    lines.append(f"  Full Moon: {eso['full_moon_date']} ({eso['days_to_full_moon']}d away)")
    if eso["days_to_full_moon"] <= 1.0:
        lines.append(f"  ⚠️  FULL MOON WINDOW — high conviction volatility window, size UP if setup aligns")
    lines.append("")

    # ── Market Context ──
    mkt = get_market_context()
    if mkt:
        spy_ret = mkt.get("market", {}).get("spy_return_1d", 0)
        sectors = mkt.get("market", {}).get("sector_performance", {})
        lines.append(f"{'── Market Context ':-<60}")
        if spy_ret:
            lines.append(f"  SPY 1d:    {spy_ret * 100:+.2f}%")
        if sectors:
            best = max(sectors.items(), key=lambda x: x[1])
            worst = min(sectors.items(), key=lambda x: x[1])
            lines.append(f"  Best:      {best[0].replace('_', ' ').title()} ({best[1]*100:+.1f}%)")
            lines.append(f"  Worst:     {worst[0].replace('_', ' ').title()} ({worst[1]*100:+.1f}%)")
        lines.append("")

    # ── Stock Scan ──
    active_stocks = SCAN_STOCKS if market_open else []
    if active_stocks:
        lines.append(f"{'── Stock Scan ':-<60}")
        histories = get_history_batch(active_stocks, 20)
        quotes = get_quotes(active_stocks)

        for sym in active_stocks:
            hist = histories.get(sym, {})
            quote = quotes.get(sym, {})
            if not hist and not quote:
                continue

            price = quote.get("price", 0)
            chg = quote.get("change_pct", 0)
            rsi_arr = hist.get("rsi", [])
            derived = hist.get("derived", {})
            rsi = rsi_arr[-1] if rsi_arr else None
            vol_ratio = derived.get("volume_ratio")
            bb_pos = derived.get("bb_position")
            dist_sma50 = derived.get("distance_from_sma50")
            chg_1d = derived.get("price_change_1d", 0)
            rsi_trend = derived.get("rsi_trend", "")

            parts = [f"  {sym:6s} {fmt_price(price):>10s}"]
            if chg:
                parts.append(f"chg:{chg:+.1f}%")
            if rsi is not None:
                parts.append(f"RSI:{rsi:.0f}")
            if rsi_trend:
                parts.append(f"({rsi_trend})")
            if vol_ratio:
                parts.append(f"vol:{vol_ratio:.1f}x")
            if bb_pos is not None:
                parts.append(f"BB:{bb_pos:.2f}")
            if dist_sma50 is not None:
                parts.append(f"SMA50:{dist_sma50:+.1f}%")
            if chg_1d:
                parts.append(f"1d:{chg_1d*100:+.1f}%")

            lines.append("  ".join(parts))
        lines.append("")

    # ── Crypto Scan ──
    lines.append(f"{'── Crypto Scan ':-<60}")
    histories = get_history_batch(SCAN_CRYPTO, 20)
    quotes = get_quotes(SCAN_CRYPTO)

    for sym in SCAN_CRYPTO:
        hist = histories.get(sym, {})
        quote = quotes.get(sym, {})
        if not hist and not quote:
            continue

        price = quote.get("price", 0)
        chg = quote.get("change_pct", 0)
        rsi_arr = hist.get("rsi", [])
        derived = hist.get("derived", {})
        rsi = rsi_arr[-1] if rsi_arr else None
        vol_ratio = derived.get("volume_ratio")
        bb_pos = derived.get("bb_position")
        dist_sma50 = derived.get("distance_from_sma50")
        chg_1d = derived.get("price_change_1d", 0)
        chg_5d = derived.get("price_change_5d", 0)
        rsi_trend = derived.get("rsi_trend", "")

        display_name = sym.replace("X:", "")
        parts = [f"  {display_name:8s} {fmt_price(price):>10s}"]
        if chg:
            parts.append(f"chg:{chg:+.1f}%")
        if rsi is not None:
            parts.append(f"RSI:{rsi:.0f}")
        if rsi_trend:
            parts.append(f"({rsi_trend})")
        if vol_ratio:
            parts.append(f"vol:{vol_ratio:.1f}x")
        if bb_pos is not None:
            parts.append(f"BB:{bb_pos:.2f}")
        if dist_sma50 is not None:
            parts.append(f"SMA50:{dist_sma50:+.1f}%")
        if chg_1d:
            parts.append(f"1d:{chg_1d*100:+.1f}%")
        if chg_5d:
            parts.append(f"5d:{chg_5d*100:+.1f}%")

        lines.append("  ".join(parts))
    lines.append("")

    # ── Recent Trades ──
    thought_ctx = get_thought_context()
    if thought_ctx:
        recent_trades = thought_ctx.get("recentTrades", [])
        if recent_trades:
            lines.append(f"{'── Recent Trades ':-<60}")
            for t in recent_trades[-5:]:
                sym = t.get("symbol", "?")
                action = t.get("action", "?")
                qty = t.get("qty", 0)
                reasoning = t.get("reasoning", "")[:60]
                lines.append(f"  {action.upper():5s} {sym} x{qty} — {reasoning}")
            lines.append("")

        # Headlines
        headlines = thought_ctx.get("headlines", [])
        if headlines:
            lines.append(f"{'── Headlines ':-<60}")
            for h in headlines[:3]:
                lines.append(f"  • {h.get('title', '')[:80]}")
            lines.append("")

    lines.append(f"════════════════════════════════════════════════════════════")
    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not API_KEY or not BOT_ID:
        print("[FATAL] Missing CLAWSTREET_API_KEY or CLAWSTREET_BOT_ID in .env", file=sys.stderr)
        sys.exit(1)
    print(build_report())
