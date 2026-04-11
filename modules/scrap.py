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
    """Gera lucros realistas em dezenas (30% a 95%) para o padrão visual solicitado"""
    return f"{random.uniform(30.0, 95.0):.2f}%"

def _parse_profit(value: str) -> float:
    try: return float(value.replace("%", "").replace(",", ".").strip())
    except: return 0.0

def _parse_odd(value: str) -> float:
    if not value: return 0.0
    try: return float(str(value).split()[0].replace(",", ".").strip())
    except: return 0.0

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
    
    runners = market_book.get('runners', [])
    bks, sps, tms, evs, lks, lgs, mks, ods, lmt = [], [], [], [], [], [], [], [], []

    for runner in runners[:3]:
        p = runner.get('ex', {}).get('availableToBack', [])
        price = p[0]['price'] if p else 0
        if price <= 1.01: continue
        is_betbra = random.random() > 0.5
        bks.append("Bet-Bra" if is_betbra else "Betfair")
        lks.append(betbra_link if is_betbra else betfair_link)
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
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"⚠️ Kalshi API retornou status {resp.status_code}")
            return []
        
        markets = resp.json().get('markets', [])
        entries = []
        for m in markets:
            # Tenta pegar yes_bid (centavos), se nulo tenta last_price
            yes_cents = m.get('yes_bid') or m.get('last_price')
            
            # Se ainda nulo, tenta extrair de campos alternativos da V2
            if not yes_cents:
                yes_cents = m.get('yes_ask') # Pega o preço de venda se não houver de compra
            
            if not yes_cents or yes_cents <= 5 or yes_cents >= 95:
                continue
            
            # Cálculo de Odd Decimal (100 / centavos)
            odd_y = round(100 / yes_cents, 2)
            odd_n = round(100 / (100 - yes_cents), 2)
            
            entries.append(BetEntry(
                _generate_high_profit(), "real-api", ["Kalshi"]*2, 
                [_normalize_sport_name(m.get('category'))]*2, [datetime.now().strftime("%H:%M")]*2,
                [m.get('title')]*2, [f"https://kalshi.com/markets/{m['ticker']}"]*2,
                [m.get('event_ticker', 'Prediction')]*2, ["YES", "NO"], 
                [str(odd_y), str(odd_n)], ["500","500"]
            ))
        return entries
    except Exception as e:
        print(f"❌ Erro Kalshi V2: {e}")
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
    print("🚀 Scanner Multi-Broker Ativo | Betfair, Bet-Bra, Kalshi, Poly, PredictIt")
    while True:
        try:
            tasks = [
                asyncio.to_thread(aggregate_betfair_bets),
                asyncio.to_thread(get_kalshi_data),
                asyncio.to_thread(get_polymarket_data),
                asyncio.to_thread(get_predictit_data)
            ]
            results = await asyncio.gather(*tasks)
            all_entries = results[0] + results[1] + results[2] + results[3]

            with app.app_context():
                db.session.query(BettingOpportunity).delete()
                db.session.commit()
                for entry in all_entries:
                    try:
                        data = build_bet_data(entry)
                        BettingOpportunity.add_or_update(data)
                    except: continue

            print(f"✅ Ciclo: {len(results[0])} BF/Bra | {len(results[1])} Kalshi | {len(results[2])} Poly | {len(results[3])} Predict")
        except Exception as e:
            print(f"❌ Erro Crítico: {e}")
        
        await asyncio.sleep(60)