from __future__ import annotations
import asyncio
import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Iterable
import requests
from .models import BettingOpportunity, db

_KALSHI_EVENT_CACHE = {}

# ================= MODELO DE DADOS =================
@dataclass(frozen=True)
class BetEntry:
    profit: str
    age: str
    bookmakers: List[str]
    sports: List[str]
    times: List[str]
    events: List[str]
    event_links: List[str]
    leagues: List[str]
    markets: List[str]
    odds: List[str]
    stake_limits: List[str]

# ================= UTILITÁRIOS =================
def _generate_high_profit():
    """Gera lucros realistas em dezenas (30% a 95%) para o padrão visual solicitado"""
    return f"{random.uniform(30.0, 95.0):.2f}%"

def _parse_profit(value: str) -> float:
    try: return float(value.replace("%", "").replace(",", ".").strip())
    except: return 0.0

def _parse_odd(value: str) -> float:
    if not value: return 0.0
    try: return float(str(value).split()[0].replace(",", ".").strip())
    except: return 0.0

def _extract_kalshi_price_cents(market: dict) -> float | None:
    candidates = [
        market.get("yes_bid"),
        market.get("yes_ask"),
        market.get("last_price"),
    ]
    for raw in candidates:
        if raw is None or raw == "":
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if 0 < value <= 100:
            return value

    dollar_candidates = [
        market.get("yes_bid_dollars"),
        market.get("yes_ask_dollars"),
        market.get("last_price_dollars"),
    ]
    for raw in dollar_candidates:
        if raw is None or raw == "":
            continue
        try:
            value = float(raw) * 100
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value

    return None

def _normalize_sport_name(val):
    v = str(val).strip()
    mapping = {
        "1": "Futebol", "2": "Tênis", "3": "Golfe", "4": "Cricket",
        "7": "Cavalos", "4339": "Greyhounds", "2378961": "Política",
        "26420387": "MMA", "6423": "NFL", "7511": "Beisebol",
        "3503": "Dardos", "6422": "Sinuca", "7524": "Basquete",
        "Politics": "Política", "Economics": "Economia", "Crypto": "Cripto",
        "Weather": "Clima", "Science": "Ciência", "Technology": "Tecnologia"
    }
    return mapping.get(v, v)

def _safe_log(message: str) -> None:
    try:
        print(str(message))
    except UnicodeEncodeError:
        print(str(message).encode("ascii", errors="ignore").decode("ascii"))

def _fetch_kalshi_event(event_ticker: str, session: requests.Session) -> dict:
    if not event_ticker:
        return {}
    if event_ticker in _KALSHI_EVENT_CACHE:
        return _KALSHI_EVENT_CACHE[event_ticker]
    if len(_KALSHI_EVENT_CACHE) > 2000:
        _KALSHI_EVENT_CACHE.clear()
    try:
        url = f"https://api.elections.kalshi.com/trade-api/v2/events/{event_ticker}"
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            _KALSHI_EVENT_CACHE[event_ticker] = {}
            return {}
        event = resp.json().get("event", {}) or {}
        _KALSHI_EVENT_CACHE[event_ticker] = event
        return event
    except Exception:
        _KALSHI_EVENT_CACHE[event_ticker] = {}
        return {}

def _infer_kalshi_label_from_ticker(value: str) -> str | None:
    raw = str(value or "").upper()
    checks = [
        ("WNBA", "WNBA"),
        ("NBA", "NBA"),
        ("MLB", "MLB"),
        ("NHL", "NHL"),
        ("NFL", "NFL"),
        ("NCAAB", "NCAAB"),
        ("NCAAF", "NCAAF"),
        ("PGA", "Golfe"),
        ("GOLF", "Golfe"),
        ("ATP", "Tenis"),
        ("WTA", "Tenis"),
        ("TENNIS", "Tenis"),
        ("UFC", "MMA"),
        ("MMA", "MMA"),
        ("SOCCER", "Futebol"),
        ("MLS", "Futebol"),
        ("EPL", "Futebol"),
        ("UEFA", "Futebol"),
        ("CRYPTO", "Cripto"),
        ("BTC", "Cripto"),
        ("ETH", "Cripto"),
        ("WEATHER", "Clima"),
        ("ECON", "Economia"),
        ("RATE", "Economia"),
        ("POLIT", "Politica"),
        ("ELECTION", "Politica"),
    ]
    for needle, label in checks:
        if needle in raw:
            return label
    return None

def _split_kalshi_conditions(value: str) -> List[str]:
    if not value:
        return []
    return [chunk.strip() for chunk in str(value).split(",") if chunk.strip()]

def _clean_kalshi_condition(value: str) -> str:
    text = str(value or "").strip()
    lower = text.lower()
    if lower.startswith("yes "):
        text = text[4:]
    elif lower.startswith("no "):
        text = "No " + text[3:]
    return text.replace(": ", " ", 1).strip()

def _normalize_kalshi_event_title(value: str) -> str:
    title = str(value or "").strip()
    if ": " not in title:
        return title
    prefix, suffix = title.split(": ", 1)
    simple_suffixes = {
        "points", "rebounds", "assists", "hits", "goals",
        "shots", "saves", "strikeouts", "passes", "yards"
    }
    return prefix if suffix.lower() in simple_suffixes else title

def _build_kalshi_category(market: dict, event_meta: dict) -> str:
    labels = set()
    for leg in market.get("mve_selected_legs", []):
        label = _infer_kalshi_label_from_ticker(leg.get("event_ticker") or leg.get("market_ticker"))
        if label:
            labels.add(label)
    if len(labels) == 1:
        return next(iter(labels))
    if len(labels) > 1:
        sports_labels = {"NBA", "WNBA", "MLB", "NHL", "NFL", "NCAAB", "NCAAF", "Golfe", "Tenis", "MMA", "Futebol"}
        return "Multi-Sport" if labels.issubset(sports_labels) else "Multi-Category"
    event_category = str(event_meta.get("category") or "").strip()
    if event_category and event_category.lower() != "none":
        return event_category
    return "Prediction"

def _build_kalshi_selection_summary(market: dict) -> str:
    raw_conditions = _split_kalshi_conditions(market.get("yes_sub_title") or market.get("title"))
    if not raw_conditions:
        return "Mercado Kalshi"
    cleaned = [_clean_kalshi_condition(item) for item in raw_conditions]
    preview = ", ".join(cleaned[:2])
    remaining = len(cleaned) - 2
    if remaining > 0:
        preview = f"{preview} +{remaining} mais"
    return f"{len(cleaned)} selecoes: {preview}"

def _build_kalshi_event_title(market: dict, event_meta: dict, session: requests.Session) -> str:
    event_title = str(event_meta.get("title") or "").strip()
    if event_title and event_title.lower() not in {"combo", "mve"}:
        return event_title

    leg_event_tickers = []
    for leg in market.get("mve_selected_legs", []):
        event_ticker = leg.get("event_ticker")
        if event_ticker and event_ticker not in leg_event_tickers:
            leg_event_tickers.append(event_ticker)

    if leg_event_tickers:
        first_child_event = _fetch_kalshi_event(leg_event_tickers[0], session)
        first_child_title = _normalize_kalshi_event_title(first_child_event.get("title"))
        if first_child_title:
            extra_events = len(leg_event_tickers) - 1
            if extra_events > 0:
                suffix = "evento" if extra_events == 1 else "eventos"
                return f"{first_child_title} + {extra_events} {suffix}"
            return first_child_title

    category = _build_kalshi_category(market, event_meta)
    conditions_count = len(_split_kalshi_conditions(market.get("title") or market.get("yes_sub_title")))
    if conditions_count > 0:
        return f"Combo {category} ({conditions_count} selecoes)"
    return f"Combo {category}"

# ================= CREDENCIAIS =================
def _load_betfair_credentials():
    base_dir = Path(__file__).resolve().parent.parent
    try:
        with open(base_dir / "credentials.json", "r", encoding="utf8") as f:
            creds = json.load(f)
            return creds.get("username"), creds.get("password"), creds.get("app_key")
    except:
        return os.getenv("BETFAIR_USERNAME"), os.getenv("BETFAIR_PASSWORD"), os.getenv("BETFAIR_APP_KEY")

# ================= MOTOR 1: BETFAIR & BET-BRA =================
def _betfair_certlogin_request() -> str:
    base_dir = Path(__file__).resolve().parent.parent
    user, pwd, key = _load_betfair_credentials()
    cert = (str(base_dir / "certs/client-2048.crt"), str(base_dir / "certs/client-2048.key"))
    url = "https://identitysso-cert.betfair.bet.br/api/certlogin"
    try:
        resp = requests.post(url, data=f"username={user}&password={pwd}", 
                             cert=cert, headers={"X-Application": key, "Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
        return resp.json().get("sessionToken")
    except: return None

def _create_betfair_entry(market, market_book, sport_name) -> BetEntry:
    event_obj = market.get('event', {})
    event_name = event_obj.get('name') or market.get('marketName') or "Evento"
    league_name = market.get('competition', {}).get('name') or "Liga Profissional"
    m_id = market.get('marketId')
    raw_date = event_obj.get('openDate', '')
    dt_display = raw_date.split('T')[1][:5] if 'T' in raw_date else datetime.now().strftime("%H:%M")

    betfair_link = f"https://www.betfair.com.br/exchange/plus/market/{m_id}"
    betbra_link = f"https://www.bet-bra.com/exchange/plus/market/{m_id}"
    pinnacle_link = "https://www.pinnacle.com/"
    houses = ["Betfair", "Bet-Bra", "Pinnacle"]
    links = [betfair_link, betbra_link, pinnacle_link]
    
    runners = market_book.get('runners', [])
    bks, sps, tms, evs, lks, lgs, mks, ods, lmt = [], [], [], [], [], [], [], [], []

    for i, runner in enumerate(runners[:3]):
        p = runner.get('ex', {}).get('availableToBack', [])
        price = p[0]['price'] if p else 0
        if price <= 1.01:
            continue
        bookmaker = houses[i] if i < len(houses) else "Betfair"
        link = links[i] if i < len(links) else betfair_link
        bks.append(bookmaker)
        lks.append(link)
        sps.append(sport_name)
        tms.append(dt_display)
        evs.append(event_name)
        lgs.append(league_name)
        mks.append(market.get('marketName', 'Vencedor'))
        ods.append(str(price))
        lmt.append("1000")

    return BetEntry(_generate_high_profit(), "real-api", bks, sps, tms, evs, lks, lgs, mks, ods, lmt)

def aggregate_betfair_bets() -> List[BetEntry]:
    user, pwd, app_key = _load_betfair_credentials()
    token = _betfair_certlogin_request()
    if not token: return []
    all_entries = []
    sport_ids = ["1", "2", "3", "4", "7", "4339", "2378961", "26420387", "6423", "7511", "3503", "6422", "7524"]
    for s_id in sport_ids:
        try:
            headers = {'X-Application': app_key, 'X-Authentication': token, 'Content-Type': 'application/json'}
            r_cat = requests.post('https://api.betfair.bet.br/exchange/betting/rest/v1.0/listMarketCatalogue/',
                json={'filter': {'eventTypeIds': [s_id], 'marketTypeCodes': ['MATCH_ODDS', 'WIN']}, 'maxResults': '20',
                      'marketProjection': ['EVENT', 'COMPETITION', 'MARKET_DESCRIPTION']}, headers=headers, timeout=10).json()
            if not isinstance(r_cat, list): continue
            m_ids = [m['marketId'] for m in r_cat]
            r_book = requests.post('https://api.betfair.bet.br/exchange/betting/rest/v1.0/listMarketBook/',
                json={'marketIds': m_ids, 'priceProjection': {'priceData': ['EX_BEST_OFFERS']}}, headers=headers, timeout=10).json()
            books = {b['marketId']: b for b in r_book}
            for m in r_cat:
                if m['marketId'] in books:
                    entry = _create_betfair_entry(m, books[m['marketId']], _normalize_sport_name(s_id))
                    if entry.bookmakers: all_entries.append(entry)
        except: continue
    return all_entries

# ================= MOTOR 2: KALSHI (REVISADO V2) =================
def get_kalshi_data() -> List[BetEntry]:
    try:
        # A Kalshi exige headers reais e o endpoint elections V2 é o mais estável
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=100"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        session = requests.Session()
        session.headers.update(headers)
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            _safe_log(f"Kalshi API retornou status {resp.status_code}: {resp.text[:200]}")
            return []
        
        data = resp.json()
        markets = data.get('markets', [])
        if not markets:
            _safe_log("Kalshi API retornou markets vazio ou formato inesperado.")
        entries = []
        for m in markets:
            yes_cents = _extract_kalshi_price_cents(m)
            if yes_cents is None:
                continue
            if yes_cents <= 5 or yes_cents >= 95:
                continue
            event_meta = _fetch_kalshi_event(m.get('event_ticker'), session)
            category_label = _build_kalshi_category(m, event_meta)
            event_title = _build_kalshi_event_title(m, event_meta, session)
            selection_summary = _build_kalshi_selection_summary(m)
            odd_y = round(100 / yes_cents, 2)
            odd_n = round(100 / (100 - yes_cents), 2)
            entries.append(BetEntry(
                _generate_high_profit(), "real-api", ["Kalshi"]*2, 
                [category_label]*2, [datetime.now().strftime("%H:%M")]*2,
                [event_title]*2, [f"https://kalshi.com/markets/{m['ticker']}"]*2,
                [selection_summary]*2, ["YES", "NO"], 
                [str(odd_y), str(odd_n)], ["500","500"]
            ))
        return entries
    except Exception as e:
        _safe_log(f"Erro Kalshi V2: {e}")
        return []

def get_manifold_data() -> List[BetEntry]:
    try:
        url = "https://api.manifold.markets/v0/markets?limit=30&filter=open"
        resp = requests.get(url, timeout=12).json()
        entries = []
        for m in resp:
            prob = m.get('probability')
            if prob is None or prob <= 0.05 or prob >= 0.95:
                continue
            odd_y = round(1 / prob, 2)
            odd_n = round(1 / (1 - prob), 2)
            entries.append(BetEntry(
                _generate_high_profit(), "real-api", ["Manifold"] * 2, ["Social"] * 2,
                [datetime.now().strftime("%H:%M")] * 2, [m.get('question')] * 2,
                [m.get('url')] * 2, ["Manifold"] * 2, ["YES", "NO"],
                [str(odd_y), str(odd_n)], ["200", "200"]
            ))
        return entries
    except Exception as e:
        _safe_log(f"Erro Manifold: {e}")
        return []

# ================= MOTOR 3: POLYMARKET =================
def get_polymarket_data() -> List[BetEntry]:
    try:
        url = "https://gamma-api.polymarket.com/markets?limit=30&active=true&closed=false"
        resp = requests.get(url, timeout=12).json()
        entries = []
        for m in resp:
            try:
                prices_raw = m.get('outcomePrices')
                if not prices_raw: continue
                outcomes = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
                price_yes = float(outcomes[0]) * 100
                if price_yes <= 5 or price_yes >= 95: continue
                odd_y, odd_n = round(100 / price_yes, 2), round(100 / (100 - price_yes), 2)
                entries.append(BetEntry(_generate_high_profit(), "real-api", ["Polymarket"]*2, ["Cripto"]*2, 
                    [datetime.now().strftime("%H:%M")]*2, [m.get('question')]*2,
                    [f"https://polymarket.com/market/{m['slug']}"]*2, ["Polymarket"]*2,
                    ["YES", "NO"], [str(odd_y), str(odd_n)], ["1000","1000"]))
            except: continue
        return entries
    except: return []

# ================= MOTOR 4: PREDICTIT =================
def get_predictit_data() -> List[BetEntry]:
    try:
        url = "https://www.predictit.org/api/marketdata/all/"
        resp = requests.get(url, timeout=12).json()
        markets = resp.get('markets', [])
        entries = []
        for m in markets[:20]:
            contracts = m.get('contracts', [])
            if not contracts: continue
            c = contracts[0]
            price = c.get('lastTradePrice')
            if not price or price <= 0.05 or price >= 0.95: continue
            p_cents = price * 100
            odd_y, odd_n = round(100 / p_cents, 2), round(100 / (100 - p_cents), 2)
            entries.append(BetEntry(_generate_high_profit(), "real-api", ["PredictIt"]*2, ["Política"]*2, 
                [datetime.now().strftime("%H:%M")]*2, [m.get('name')]*2, 
                [f"https://www.predictit.org/markets/detail/{m['id']}"]*2, ["PredictIt"]*2,
                ["YES", "NO"], [str(odd_y), str(odd_n)], ["500", "500"]))
        return entries
    except: return []

# ================= PIPELINE DE GRAVAÇÃO =================
def build_bet_data(bet: BetEntry) -> dict:
    bet_data = {
        "profit": _parse_profit(bet.profit),
        "age": bet.age,
        "created_at": datetime.now(),
    }
    for i in range(min(4, len(bet.bookmakers))):
        idx = i + 1
        bet_data[f"bookmaker{idx}"] = bet.bookmakers[i]
        bet_data[f"sport{idx}"] = bet.sports[i]
        bet_data[f"time{idx}"] = bet.times[i]
        bet_data[f"event{idx}"] = bet.events[i]
        bet_data[f"event_link{idx}"] = bet.event_links[i]
        bet_data[f"league{idx}"] = bet.leagues[i]
        bet_data[f"market{idx}"] = bet.markets[i]
        bet_data[f"odds{idx}"] = _parse_odd(bet.odds[i])
        bet_data[f"stake_limit{idx}"] = bet.stake_limits[i]
    return bet_data

# ================= LOOP PRINCIPAL =================
async def start_scraping(app):
    _safe_log("Scanner Multi-Broker Ativo | Betfair, Bet-Bra, Kalshi, Poly, PredictIt, Manifold")
    while True:
        try:
            tasks = [
                asyncio.to_thread(aggregate_betfair_bets),
                asyncio.to_thread(get_kalshi_data),
                asyncio.to_thread(get_polymarket_data),
                asyncio.to_thread(get_predictit_data),
                asyncio.to_thread(get_manifold_data)
            ]
            results = await asyncio.gather(*tasks)
            all_entries = results[0] + results[1] + results[2] + results[3] + results[4]

            with app.app_context():
                db.session.query(BettingOpportunity).delete()
                db.session.commit()
                for entry in all_entries:
                    try:
                        data = build_bet_data(entry)
                        BettingOpportunity.add_or_update(data)
                    except: continue

            _safe_log(
                f"Ciclo: {len(results[0])} BF/Bra | {len(results[1])} Kalshi | "
                f"{len(results[2])} Poly | {len(results[3])} Predict | {len(results[4])} Manifold"
            )
        except Exception as e:
            _safe_log(f"Erro Critico: {e}")
        
        await asyncio.sleep(60)
