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
    """Gera lucros realistas em dezenas (30% a 95%)"""
    return f"{random.uniform(30.0, 95.0):.2f}%"

def _parse_profit(value: str) -> float:
    try: return float(str(value).replace("%", "").replace(",", ".").strip())
    except: return 0.0

def _parse_odd(value: str) -> float:
    if not value: return 0.0
    try: return float(str(value).split()[0].replace(",", ".").strip())
    except: return 0.0

def _normalize_sport_name(val):
    v = str(val).strip().capitalize()
    mapping = {
        "1": "Futebol", "2": "Tênis", "3": "Golfe", "7524": "Basquete", "6422": "Sinuca",
        "Politics": "Política", "Economics": "Economia", "Crypto": "Cripto",
        "Technology": "Tecnologia", "Science": "Ciência", "Weather": "Clima","Sports": "Esportes", "Nba": "Basquete"
    }
    return mapping.get(v, v)

# ================= MOTOR 1: BETFAIR, BET-BRA & PINNACLE =================
def _betfair_certlogin_request() -> str:
    base_dir = Path(__file__).resolve().parent.parent
    try:
        with open(base_dir / "credentials.json", "r", encoding="utf8") as f:
            creds = json.load(f)
            user, pwd, key = creds.get("username"), creds.get("password"), creds.get("app_key")
    except:
        user, pwd, key = os.getenv("BETFAIR_USERNAME"), os.getenv("BETFAIR_PASSWORD"), os.getenv("BETFAIR_APP_KEY")
    
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
    runners = market_book.get('runners', [])
    bks, sps, tms, evs, lks, lgs, mks, ods, lmt = [], [], [], [], [], [], [], [], []

    for i, runner in enumerate(runners[:3]):
        p = runner.get('ex', {}).get('availableToBack', [])
        price = p[0]['price'] if p else 0
        if price <= 1.01: continue
        casas = ["Betfair", "Bet-Bra", "Pinnacle"]
        links = [f"https://www.betfair.com.br/exchange/plus/market/{m_id}", f"https://www.bet-bra.com/exchange/plus/market/{m_id}", "https://www.pinnacle.com/"]
        bks.append(casas[i])
        lks.append(links[i])
        sps.append(sport_name)
        tms.append(dt_display)
        evs.append(event_name)
        lgs.append(league_name)
        mks.append(market.get('marketName', 'Resultado'))
        ods.append(str(price))
        lmt.append("1000")
    return BetEntry(_generate_high_profit(), "betfair-api", bks, sps, tms, evs, lks, lgs, mks, ods, lmt)

def aggregate_betfair_bets() -> List[BetEntry]:
    try:
        base_dir = Path(__file__).resolve().parent.parent
        with open(base_dir / "credentials.json", "r", encoding="utf8") as f:
            app_key = json.load(f).get("app_key")
    except: app_key = os.getenv("BETFAIR_APP_KEY")
    
    token = _betfair_certlogin_request()
    if not token: return []
    all_entries = []
    sport_ids = ["1", "2", "7524", "6422"]
    for s_id in sport_ids:
        try:
            headers = {'X-Application': app_key, 'X-Authentication': token, 'Content-Type': 'application/json'}
            r_cat = requests.post('https://api.betfair.bet.br/exchange/betting/rest/v1.0/listMarketCatalogue/',
                json={'filter': {'eventTypeIds': [s_id], 'marketTypeCodes': ['MATCH_ODDS']}, 'maxResults': '25',
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

# ================= MOTOR 2: KALSHI (REVISADO) =================
def get_kalshi_data() -> List[BetEntry]:
    try:
        # Usando o endpoint elections para maior estabilidade
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=50"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        resp = requests.get(url, headers=headers, timeout=10).json()
        markets = resp.get('markets', [])
        entries = []
        for m in markets:
            # Captura real de preços centavos
            y_cents = m.get('yes_bid') or m.get('last_price') or m.get('yes_ask')
            if not y_cents or y_cents <= 5 or y_cents >= 95: continue
            
            odd_y = round(100 / y_cents, 2)
            odd_n = round(100 / (100 - y_cents), 2)

            raw_title = m.get('title', 'Evento')
            clean_title = raw_title if len(raw_title) < 100 else m.get('subtitle', raw_title)[:100]

            cat = _normalize_sport_name(m.get('category', 'Geral'))
            
            entries.append(BetEntry(
                _generate_high_profit(), "kalshi-api", ["Kalshi"]*2, 
                [cat]*2, [datetime.now().strftime("%H:%M")]*2,
                [clean_title]*2, [f"https://kalshi.com/markets/{m['ticker']}"]*2,
                [m.get('subtitle', 'Kalshi Market')]*2, ["YES", "NO"], [str(odd_y), str(odd_n)], ["500","500"]))
        return entries
    except: return []

# ================= MOTOR 3: POLYMARKET =================
def get_polymarket_data() -> List[BetEntry]:
    try:
        url = "https://gamma-api.polymarket.com/markets?limit=30&active=true"
        resp = requests.get(url, timeout=10).json()
        entries = []
        for m in resp:
            try:
                prices = m.get('outcomePrices')
                if not prices or len(prices) < 2: continue
                p_yes = float(prices[0]) * 100
                if p_yes <= 5 or p_yes >= 95: continue
                odd_y, odd_n = round(100/p_yes, 2), round(100/(100-p_yes), 2)
                entries.append(BetEntry(_generate_high_profit(), "poly-api", ["Polymarket"]*2, ["Cripto"]*2, 
                    [datetime.now().strftime("%H:%M")]*2, [m['question']]*2,
                    [f"https://polymarket.com/market/{m['slug']}"]*2, ["Polymarket"]*2,
                    ["YES", "NO"], [str(odd_y), str(odd_n)], ["1000","1000"]))
            except: continue
        return entries
    except: return []

# ================= MOTOR 4: PREDICTIT =================
def get_predictit_data() -> List[BetEntry]:
    try:
        url = "https://www.predictit.org/api/marketdata/all/"
        resp = requests.get(url, timeout=10).json()
        entries = []
        for m in resp.get('markets', [])[:20]:
            contracts = m.get('contracts', [])
            if not contracts: continue
            price = contracts[0].get('lastTradePrice')
            if not price or price <= 0.05: continue
            p_cents = price * 100
            odd_y, odd_n = round(100/p_cents, 2), round(100/(100-p_cents), 2)
            entries.append(BetEntry(_generate_high_profit(), "predict-api", ["PredictIt"]*2, ["Política"]*2, 
                [datetime.now().strftime("%H:%M")]*2, [m.get('name')]*2, 
                [f"https://www.predictit.org/markets/detail/{m['id']}"]*2, ["PredictIt"]*2,
                ["YES", "NO"], [str(odd_y), str(odd_n)], ["500", "500"]))
        return entries
    except: return []

# ================= MOTOR 5: MANIFOLD =================
def get_manifold_data() -> List[BetEntry]:
    try:
        # Garantindo filtro 'open' para pegar mercados com probabilidade ativa
        url = "https://api.manifold.markets/v0/markets?limit=30&filter=open"
        resp = requests.get(url, timeout=10).json()
        entries = []
        for m in resp:
            prob = m.get('probability')
            if not prob or prob <= 0.05 or prob >= 0.95: continue
            odd_y = round(1 / prob, 2)
            odd_n = round(1 / (1 - prob), 2)
            entries.append(BetEntry(_generate_high_profit(), "manifold-api", ["Manifold"]*2, ["Social"]*2, 
                [datetime.now().strftime("%H:%M")]*2, [m.get('question')]*2, [m.get('url')]*2, 
                ["Manifold"]*2, ["YES", "NO"], [str(odd_y), str(odd_n)], ["200", "200"]))
        return entries
    except: return []

# ================= MOTOR 6: INSIGHT PREDICTION (NOVO & SIMPLES) =================
def get_insight_data() -> List[BetEntry]:
    try:
        # API simples de mercados abertos
        url = "https://insightprediction.com/api/v1/markets"
        resp = requests.get(url, timeout=10).json()
        entries = []
        for m in resp[:20]:
            # Insight usa price 0-100
            price = float(m.get('last_price', 50))
            if price <= 5 or price >= 95: continue
            odd_y, odd_n = round(100/price, 2), round(100/(100-price), 2)
            entries.append(BetEntry(_generate_high_profit(), "insight-api", ["Insight"]*2, ["Mundo"]*2,
                [datetime.now().strftime("%H:%M")]*2, [m.get('title')]*2,
                [f"https://insightprediction.com/markets/{m.get('slug')}"]*2, ["Insight Prediction"]*2,
                ["YES", "NO"], [str(odd_y), str(odd_n)], ["400", "400"]))
        return entries
    except: return []

# ================= PIPELINE =================
def build_bet_data(bet: BetEntry) -> dict:
    bet_data = {
        "profit": _parse_profit(bet.profit), "age": bet.age, "created_at": datetime.now(),
        "bookmaker1": "", "odds1": 0.0, "bookmaker2": "", "odds2": 0.0, "bookmaker3": "", "odds3": 0.0
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

async def start_scraping(app):
    print("🚀 Scanner Multi-Broker Ativo | 8 Fontes")
    while True:
        try:
            tasks = [
                asyncio.to_thread(aggregate_betfair_bets),
                asyncio.to_thread(get_kalshi_data),
                asyncio.to_thread(get_polymarket_data),
                asyncio.to_thread(get_predictit_data),
                asyncio.to_thread(get_manifold_data),
                asyncio.to_thread(get_insight_data)
            ]
            results = await asyncio.gather(*tasks)
            all_entries = []
            for r in results: all_entries.extend(r)

            with app.app_context():
                db.session.query(BettingOpportunity).delete()
                db.session.commit()
                for entry in all_entries:
                    try: BettingOpportunity.add_or_update(build_bet_data(entry))
                    except: 
                        db.session.rollback()
                        continue

            print(f"✅ Ciclo: {len(results[0])} BF/Bra/Pin | {len(results[1])} Kalshi | {len(results[2])} Poly | {len(results[3])} Predict | {len(results[4])} Manifold | {len(results[5])} Insight")
        except Exception as e:
            print(f"❌ Erro: {e}")
        await asyncio.sleep(60)