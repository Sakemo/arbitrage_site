import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.scrap import aggregate_betfair_bets

try:
    bets = aggregate_betfair_bets(max_results=5)
    print('✅ aggregate_betfair_bets returned', len(bets), 'entries')
    for idx, bet in enumerate(bets[:3], 1):
        print(f'{idx}. age={bet.age}, profit={bet.profit}, bookmakers={bet.bookmakers}, events={bet.events[:1]}')
except Exception as exc:
    print('❌ aggregate_betfair_bets failed:', exc)
    raise
