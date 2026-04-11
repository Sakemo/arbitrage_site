import requests
from datetime import datetime
import os

MTGREEN_TOKEN = '7578534222:AAHCc4zAFPaUyiaOWA99NAqHaCvSwV1x87o'
MTGREEN_CHAT_ID = '-1002827036502'

# Keep track of bets already sent to avoid duplicates (store unique bet ids, max 100)
bets_enviadas = []
MAX_BETS_HISTORY = 100

# Rate limit configuration: maximum signals allowed per hour, reset at every hour and at 00:00 UTC
MAX_SIGNALS_PER_HOUR = 2
_sent_hours = {}
_last_reset_date = None

script_dir = os.path.dirname(os.path.abspath(__file__))
def enviar_telegram_mtgreen(bet):
    print('[DEBUG] Função enviar_telegram_mtgreen chamada')
    """Send a bet notification to Telegram if it fits the desired filters.

    Filters:
        1. Sport must be e-futebol / e-soccer / futebol virtual.
        2. Profit must be greater than 3 %.
    """
    # Accepted sports keywords (normalized to lower-case)
    esportes_aceitos = [
        'futebol', 'tênis', 'tenis', 'basquete', 'vôlei', 'volei', 'mma', 'ufc'
    ]

    # Accepted bookmakers (normalized to lower-case)
    casas_aceitas = [
        'stake', 'betano', 'esportivabet', 'aposta online', 'novibet', 'bet365',
        'superbet', 'sportingbet', 'betnacional', 'vbet', 'cassino pix', '7kbet', 'pinnacle'
    ]

    # ----- SPORT FILTER -----
    sport = bet.sports[0].strip().lower() if bet.sports and bet.sports[0] else ''
    print(f'[DEBUG] Esporte detectado: {sport}')
    if not any(e in sport for e in esportes_aceitos):
        #print('[DEBUG] Não passou no filtro de esportes aceitos')
        return  # Sport not accepted

    # ----- BOOKMAKER FILTER -----
    if not any(bk.lower() in casas_aceitas for bk in bet.bookmakers):
        #print(f'[DEBUG] Bookmakers detectados: {[bk.lower() for bk in bet.bookmakers]}')
        #print('[DEBUG] Não passou no filtro de casas aceitas')
        return  # Bookmaker not in accepted list

    # ----- TIME FILTER (only bets from last 24h) -----
    # bet.age examples: '3h 12m', '45m', '1d 2h', etc.
    age_str = getattr(bet, 'age', '') or ''
    #print(f'[DEBUG] Age detectado: {age_str}')
    if 'd' in age_str.lower():
        #print('[DEBUG] Age contém "d", aposta antiga demais')
        return
    try:
        hours_part = 0
        for part in age_str.split():
            if 'h' in part:
                hours_part = int(part.replace('h', ''))
        #print(f'[DEBUG] Horas detectadas: {hours_part}')
        if hours_part >= 24:
            #print('[DEBUG] Age >= 24h, aposta antiga demais')
            return
    except Exception as e:
        #print(f'[DEBUG] Erro ao interpretar age: {e}')
        pass

    # ----- PROFIT FILTER -----
    try:
        lucro = float(bet.profit.replace('%', '').replace(',', '.'))
        #print(f'[DEBUG] Lucro detectado: {lucro}')
    except Exception as e:
        #print(f'[DEBUG] Erro ao converter lucro: {e}')
        return  # Could not parse profit

    if lucro <= 0:
        #print('[DEBUG] Lucro menor ou igual a zero, não envia')
        return  # Profit threshold not met

    casas = f"{bet.bookmakers[0]} x {bet.bookmakers[1] if len(bet.bookmakers) > 1 else ''}".strip()

    mensagem = f"""LUCRO: {bet.profit} ✅\n\n
🟢 {bet.bookmakers[0]}: @{bet.odds[0]} - <a href=\"{bet.event_links[0]}\">Clique aqui</a>
⚪ Aposta: {bet.markets[0]}

🟢 {bet.bookmakers[1]}: @{bet.odds[1]} - <a href=\"{bet.event_links[1]}\">Clique aqui</a>
⚪ Aposta: {bet.markets[1]}
"""
    payload = {
        'chat_id': MTGREEN_CHAT_ID,
        'text': mensagem,
        'parse_mode': 'Markdown'
    }
    # Rate-limiting: 1 per 30 minutes
    from datetime import timezone
    now = datetime.now(timezone.utc)
    global _sent_hours, _last_reset_date
    today = now.date()
    hour = now.hour
    # Reset all counters at 00:00 UTC
    if _last_reset_date != today:
        _sent_hours = {}
        _last_reset_date = today
    # Clean old hours (keep only this hour)
    _sent_hours = {h: c for h, c in _sent_hours.items() if h == hour}
    count_this_hour = _sent_hours.get(hour, 0)
    if count_this_hour >= MAX_SIGNALS_PER_HOUR:
        #print('[DEBUG] Limite horário de sinais atingido')
        return  # Hourly limit reached

    # Unique bet id based on main fields (event, bookmakers, odds, time)
    bet_id = f"{bet.events[0]}_{bet.bookmakers[0]}_{bet.bookmakers[1]}_{bet.odds[0]}_{bet.odds[1]}_{bet.times[0]}"
    if bet_id not in bets_enviadas:
        #print('[DEBUG] Enviando mensagem para o Telegram MTGREEN...')
        try:
            with open(os.path.join(script_dir, "../assets/img/sinal_telegram.jpg"), "rb") as img_file:
                
                response = requests.post(
                    f"https://api.telegram.org/bot{MTGREEN_TOKEN}/sendPhoto",
                    data={
                        "chat_id": MTGREEN_CHAT_ID,
                        "caption": mensagem,
                        "parse_mode": "HTML"
                    },
                    files={"photo": img_file}
                )
            #print(f"[DEBUG] Status code do Telegram: {response.status_code}")
            #print(f"[DEBUG] Resposta do Telegram: {response.text}")
        except Exception as e:
            print(f"[DEBUG] Erro ao enviar mensagem para o Telegram: {e}")
        bets_enviadas.append(bet_id)
        # Mantém só os últimos 100 bets para não crescer indefinidamente
        if len(bets_enviadas) > MAX_BETS_HISTORY:
            bets_enviadas.pop(0)
        _sent_hours[hour] = _sent_hours.get(hour, 0) + 1
        print("Bet sent to MTGREEN Telegram")
    else:
        print('[DEBUG] Bet já enviada, não repete.')

class FakeBet:
    def __init__(self, profit, age, bookmakers, sports, times, events, event_links, leagues, markets, odds, stake_limits):
        self.profit = profit
        self.age = age
        self.bookmakers = bookmakers
        self.sports = sports
        self.times = times
        self.events = events
        self.event_links = event_links
        self.leagues = leagues
        self.markets = markets
        self.odds = odds
        self.stake_limits = stake_limits

# fake_bet = FakeBet(
#     profit="5.0%",
#     age="12h 2m",
#     bookmakers=["Stake", "Betano"],
#     sports=["Futebol"],
#     times=["12:30"],
#     events=["Real Madrid vs Barcelona"],
#     event_links=["https://pt.surebet.com/surebets","https://pt.surebet.com/surebets","https://pt.surebet.com/surebets"],
#     leagues=["La Liga"],
#     markets=["1 x 2","1 x 2","1 x 2"],
#     odds=["1.85", "2.00","2.00"],
#     stake_limits=["100", "200","200"]
# )
# enviar_telegram_mtgreen(fake_bet)
    