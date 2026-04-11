import requests
import os

BOT_TOKEN = '7524931948:AAF8yz32GdOMIHuEiMhLFaulAFMOv1NveGs'
CHAT_ID = "-1002975530829" #'-1002871799623' antigo
bets_enviadas = []
script_dir = os.path.dirname(os.path.abspath(__file__))





def enviar_telegram(bet):
    print("[DEBUG] Função enviar_telegram chamada")
    # Filtro: só sinais de e-futebol/esoccer/futebol virtual e lucro > 3%
    esportes_aceitos = [
        'e-futebol', 'efutebol', 'esoccer', 'e-soccer', 'futebol virtual', 'virtual football', 'efootball', 'e soccer', 'E-Futebol'
    ]
    sport = bet.sports[0].strip().lower() if bet.sports and bet.sports[0] else ''
    if not any(e in sport for e in esportes_aceitos):
        print("[DEBUG] Não passou no filtro de esportes aceitos")
        return  # Não é e-futebol/esoccer/virtual
    try:
        lucro = float(bet.profit.replace('%', '').replace(',', '.'))
    except Exception:
        return  # Não conseguiu converter lucro
    if lucro <= 3.0:
        print("[DEBUG] Lucro menor ou igual a 3.0, não envia")
        return  # Só sinais com lucro acima de 3%

    casas = f"{bet.bookmakers[0]} x {bet.bookmakers[1] if len(bet.bookmakers) > 1 else ''}".strip()
    mensagem = f"""
⚫️ ARBPRO FIFA

🏘️ Casas: {casas}
🤑 LUCRO: {bet.profit}
▶️ {bet.events[0]}
🏆 {bet.sports[0]} / {bet.leagues[0]}
🕑 Data: {bet.times[0]}
⚫ {bet.bookmakers[0]}: @{bet.odds[0]} - [Clique aqui]({bet.event_links[0]})
⚪ Aposta: {bet.markets[0]}
"""
    if len(bet.bookmakers) > 1:
        mensagem += f"""
⚫ {bet.bookmakers[1]}: @{bet.odds[1]} - [Clique aqui]({bet.event_links[1]})
⚪ Aposta: {bet.markets[1]}
"""
    payload = {
        'chat_id': CHAT_ID,
        'text': mensagem,
        'parse_mode': 'Markdown'
    }
    if bet not in bets_enviadas:
        print("[DEBUG] Enviando mensagem para o Telegram...")
        try:
            with open(os.path.join(script_dir, "../assets/img/mtfifa.jpeg"), "rb") as img_file:
                response = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    data={
                        "chat_id": CHAT_ID,
                        "caption": mensagem,
                        "parse_mode": "Markdown"
                    },
                    files={"photo": img_file}
                )
            print(f"[DEBUG] Status code do Telegram: {response.status_code}")
            print(f"[DEBUG] Resposta do Telegram: {response.text}")
        except Exception as e:
            print(f"[DEBUG] Erro ao enviar mensagem para o Telegram: {e}")
        bets_enviadas.append(bet)
    else:
        print("[DEBUG] Bet já enviada, não repete.")

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
#     age="1h 2m",
#     bookmakers=["Stake", "Betano"],
#     sports=["EFutebol"],
#     times=["12:30"],
#     events=["Real Madrid vs Barcelona"],
#     event_links=["https://pt.surebet.com/surebets","https://pt.surebet.com/surebets","https://pt.surebet.com/surebets"],
#     leagues=["La Liga"],
#     markets=["1 x 2","1 x 2","1 x 2"],
#     odds=["1.85", "2.00","2.00"],
#     stake_limits=["100", "200","200"]
# )
# enviar_telegram(fake_bet)

