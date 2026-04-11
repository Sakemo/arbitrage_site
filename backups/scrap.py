from .models import db, BettingOpportunity
import asyncio
from dataclasses import dataclass
from typing import List
from datetime import datetime
from playwright.async_api import async_playwright
import random
from modules.telegram_utils import enviar_telegram
from modules.telegram_mt_green import enviar_telegram_mtgreen
import time
import os
import json


# Lista simples de user-agents reais para rotacionar
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/121.0"
]
EMAIL = "yifage7831@hostbyt.com"
PASSWORD = "12345cima"

# ================= MODELO DE DADOS =================
@dataclass
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

def store_bet_in_database(bet: BetEntry, app) -> bool:
    with app.app_context():
        try:
            formatted_times = [t[:5] + ' ' + t[5:] for t in bet.times]
            profit_value = float(bet.profit.replace('%', '').replace(',', '.'))

            bet_data = {
                'profit': profit_value,
                'age': bet.age,
                'created_at': datetime.now()
            }

            for i in range(4):
                if i < len(bet.bookmakers):
                    odds_value = float(bet.odds[i].split()[0]) if bet.odds[i] else 0.0
                    bet_data.update({
                        f'bookmaker{i+1}': bet.bookmakers[i],
                        f'sport{i+1}': bet.sports[i],
                        f'time{i+1}': formatted_times[i],
                        f'event{i+1}': bet.events[i],
                        f'event_link{i+1}': bet.event_links[i],
                        f'league{i+1}': bet.leagues[i],
                        f'market{i+1}': bet.markets[i],
                        f'odds{i+1}': odds_value,
                        f'stake_limit{i+1}': bet.stake_limits[i]
                    })
                stored_bet = BettingOpportunity.add_or_update(bet_data)
            return True
        except Exception as e:
            print(f"Erro ao armazenar aposta: {e}")
            return False

# Function to get the table data using Playwright
async def get_table_data_from_page(page) -> List[BetEntry]:
    print("Getting table data...")
    bet_entries = []
    base_url = "https://pt.surebet.com"
    # Recarrega a página de surebets
    await page.goto("https://pt.surebet.com/surebets")
    await page.wait_for_selector('tbody.surebet_record')

    html = await page.content()
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', id='surebets-table')
    if not table:
        print("Table not found!")
        return []
    rows = table.find_all('tr')
    current_bet = None
    bookmakers = []
    sports = []
    times = []
    events = []
    event_links = []
    leagues = []
    markets = []
    odds_list = []
    stake_limits = []
    for row in rows:
        if row.find('th'):
            continue
        profit_span = row.find('span', class_='profit')
        if profit_span:
            if current_bet:
                bet_entry = BetEntry(
                    profit=current_bet['profit'],
                    age=current_bet['age'],
                    bookmakers=bookmakers,
                    sports=sports,
                    times=times,
                    events=events,
                    event_links=event_links,
                    leagues=leagues,
                    markets=markets,
                    odds=odds_list,
                    stake_limits=stake_limits
                )
                bet_entries.append(bet_entry)
            current_bet = {
                'profit': profit_span.text.strip(),
                'age': row.find('span', class_='age').text.strip()
            }
            bookmakers = []
            sports = []
            times = []
            events = []
            event_links = []
            leagues = []
            markets = []
            odds_list = []
            stake_limits = []
        bookmaker_cell = row.find('td', class_='booker')
        if bookmaker_cell:
            if bookmaker_cell.find('a'):
                bookmakers.append(bookmaker_cell.find('a').text.strip())
            sport_span = bookmaker_cell.find('span', class_='minor')
            if sport_span:
                sports.append(sport_span.text.strip())
        time_cell = row.find('td', class_='time')
        if time_cell and time_cell.find('abbr'):
            times.append(time_cell.find('abbr').text.strip())
        event_cell = row.find('td', class_='event')
        if event_cell:
            event_link = event_cell.find('a')
            if event_link:
                events.append(event_link.text.strip())
                relative_path = event_link.get('href', '')
                full_url = base_url + relative_path if relative_path else ''
                event_links.append(full_url)
            else:
                events.append('')
                event_links.append('')
            leagues.append(event_cell.find('span', class_='minor').text.strip() if event_cell.find('span', class_='minor') else '')
        market_cell = row.find('td', class_='coeff')
        if market_cell and market_cell.find('abbr'):
            markets.append(market_cell.find('abbr').text.strip())
        odds_cell = row.find('td', class_='value')
        if odds_cell:
            odds_value = odds_cell.find('a', class_='value_link')
            odds_list.append(odds_value.text.strip() if odds_value else '')
            stake_limit = odds_cell.find('span', class_='limit')
            stake_limits.append(stake_limit.text.strip() if stake_limit else '')
    if current_bet:
        bet_entry = BetEntry(
            profit=current_bet['profit'],
            age=current_bet['age'],
            bookmakers=bookmakers,
            sports=sports,
            times=times,
            events=events,
            event_links=event_links,
            leagues=leagues,
            markets=markets,
            odds=odds_list,
            stake_limits=stake_limits
        )
        bet_entries.append(bet_entry)
    return bet_entries

# Function to start scraping in a loop
async def start_scraping(app):
    print("Starting scraping...")
    async with async_playwright() as p:
        

        # Rotaciona User-Agent e Accept-Language
        user_agent = random.choice(USER_AGENTS)
        accept_language = random.choice(["pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7", "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7"])

        # Argumentos extras para mascarar headless
        extra_args = [
            "--disable-blink-features=AutomationControlled",
            "--start-minimized",
            "--disable-infobars",
            "--window-position=0,0",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]

        context = await p.chromium.launch_persistent_context(
            user_data_dir="playwright_profile",
            headless=False,  # Evita detecção simples de headless
            args=extra_args,
            locale="pt-BR",
            user_agent=user_agent,
            viewport={"width": 1366, "height": 768},
            slow_mo=random.randint(100, 300),
        )
        page = context.pages[0] if context.pages else await context.new_page()

        # Injeção de cookies reais, se existir arquivo cookies.json
        cookies_path = "cookies.json"
        if os.path.exists(cookies_path):
            try:
                with open(cookies_path, "r", encoding="utf8") as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print("[ANTI-BOT] Cookies reais injetados.")
            except Exception as e:
                print(f"[ANTI-BOT] Falha ao injetar cookies: {e}")

        # Mascarar navigator.webdriver e outros sinais JS
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        await page.add_init_script("window.chrome = { runtime: {} }")
        await page.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en']})")
        await page.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]})")

        # Define headers adicionais
        await page.set_extra_http_headers({
            "Accept-Language": accept_language,
            "Referer": "https://pt.surebet.com/",
            "Connection": "keep-alive"
        })

        # Pequeno delay inicial simulando "usuário lendo"
        await asyncio.sleep(random.uniform(2.0, 5.0))

        # Simula movimento do mouse e scroll
        await page.mouse.move(random.randint(100, 800), random.randint(100, 600), steps=random.randint(5, 20))
        await page.evaluate("window.scrollBy(0, 300)")
        await asyncio.sleep(random.uniform(0.5, 2.0))

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"Tentativa de login {attempt}/{max_attempts}")
            await page.goto("https://pt.surebet.com/users/sign_in")
            print(page.url)
            await asyncio.sleep(random.uniform(1.0, 2.5))  # Delay após carregar página de login

            # Verifica se já está logado (mensagem "Você já está logado.")
            try:
                elem = await page.query_selector('xpath=//*[@id="base"]/main/div[2]')
                if elem:
                    text = await elem.inner_text()
                    print(f"[DEBUG] Texto do aviso de login: {text}")
                    if "Você já está logado." in text:
                        print("[DEBUG] Usuário já está logado, pulando login!")
                        break  # já logado, sai do loop de login
            except Exception as e:
                print(f"[DEBUG] Erro ao verificar aviso de login: {e}")

            # Simula foco, digitação e movimento do mouse nos campos
            await page.focus('input[name="user[email]"]')
            await page.mouse.move(random.randint(200, 600), random.randint(300, 500), steps=random.randint(3, 8))
            await asyncio.sleep(random.uniform(0.2, 0.6))
            await page.type('input[name="user[email]"]', EMAIL, delay=random.randint(80, 170))
            await asyncio.sleep(random.uniform(1.5, 3.5))
            await page.focus('input[name="user[password]"]')
            await page.mouse.move(random.randint(400, 900), random.randint(350, 600), steps=random.randint(3, 8))
            await asyncio.sleep(random.uniform(0.2, 0.6))
            await page.type('input[name="user[password]"]', PASSWORD, delay=random.randint(80, 170))
            await asyncio.sleep(random.uniform(2.0, 5.0))
            async with page.expect_navigation():
                await page.click('input[name="commit"]')
            current_url = page.url
            print("URL após login:", current_url)
            if "/plan/buy" in current_url:
                await page.goto("https://pt.surebet.com/")
                break
            elif attempt == max_attempts:
                raise Exception("Acesso negado: Redirecionado para página de compra após múltiplas tentativas. Verifique o login ou a assinatura.")
            else:
                print("Redirecionado para página de compra, tentando novamente...")

            # Pequeno delay pós-login simulando "usuário esperando carregamento"
            await asyncio.sleep(random.uniform(1.0, 2.5))

        # Após login bem-sucedido

        await page.wait_for_url("**/surebets", timeout=10000)
        await asyncio.sleep(random.uniform(1.0, 2.0))  # Delay pós-carregamento

        # Simula interação com filtros (como no script Node.js)
        # try:
        #     selector3 = 'label[for="group-size-3"] input'
        #     checked = await page.eval_on_selector(selector3, "el => el.checked")
        #     if checked:
        #         await page.click('label[for="group-size-3"]')
        #         await asyncio.sleep(random.uniform(0.5, 1.2))
        #         await page.click('button[type="submit"]')  # botão Filtrar
        #         await asyncio.sleep(random.uniform(2.0, 4.0))
        #         print('☑️ Apenas 2 seleções ativado')
        # except Exception as e:
        #     print('⚠️ Filtro não aplicado:', str(e))

        # Loop de scraping mantendo a sessão
        while True:
            try:
                # Simula scroll e mouse antes de cada coleta
                await page.mouse.move(random.randint(200, 1000), random.randint(200, 700), steps=random.randint(8, 20))
                await page.evaluate(f"window.scrollBy(0, {random.randint(100, 700)})")
                await asyncio.sleep(random.uniform(0.5, 1.5))

                with app.app_context():
                    bets = await get_table_data_from_page(page)
                    sent_mtgreen = False
                    for bet in bets:
                        success = store_bet_in_database(bet, app)
                        if success:
                            enviar_telegram(bet)
                            if not sent_mtgreen:
                                enviar_telegram_mtgreen(bet)
                                sent_mtgreen = True
                # Delay humanizado entre ciclos
                await asyncio.sleep(random.randint(50, 90) + random.uniform(0, 8))
            except Exception as e:
                print(f"Error in scraping loop: {str(e)}")
                await asyncio.sleep(random.randint(50, 90) + random.uniform(0, 8))

        