import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import requests
from modules.scrap import _betfair_certlogin_request

try:
    token = _betfair_certlogin_request()
    print('session token obtained:', token[:10] + '...')
    url = 'https://api.betfair.bet.br/exchange/betting/rest/v1.0/listMarketCatalogue/'
    headers = {
        'X-Application': __import__('os').getenv('BETFAIR_APP_KEY'),
        'X-Authentication': token,
        'Content-Type': 'application/json',
    }
    payload = {
        'filter': {
            'eventTypeIds': ['1'],
            'marketCountries': ['BR'],
            'marketTypeCodes': ['MATCH_ODDS'],
            'inPlayOnly': False,
        },
        'maxResults': '5',
        'marketProjection': ['COMPETITION', 'EVENT', 'RUNNER_METADATA', 'MARKET_DESCRIPTION'],
    }
    print('Querying listMarketCatalogue...')
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    print('HTTP', resp.status_code)
    print(resp.text[:1000])
    catalog = resp.json()
    if not catalog:
        print('No market catalogue returned')
        sys.exit(1)
    market_ids = [item['marketId'] for item in catalog[:5]]
    print('market ids:', market_ids)

    url2 = 'https://api.betfair.bet.br/exchange/betting/rest/v1.0/listMarketBook/'
    payload2 = {
        'marketIds': market_ids,
        'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
    }
    print('Querying listMarketBook minimal...')
    resp2 = requests.post(url2, json=payload2, headers=headers, timeout=30)
    print('HTTP', resp2.status_code)
    print(resp2.text[:2000])

    url3 = 'https://api.betfair.bet.br/exchange/betting/rest/v1.0/listMarketBook'
    payload3 = {
        'marketIds': market_ids,
        'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
    }
    print('Querying listMarketBook without trailing slash...')
    resp3 = requests.post(url3, json=payload3, headers=headers, timeout=30)
    print('HTTP', resp3.status_code)
    print(resp3.text[:2000])
except Exception as exc:
    print('ERROR:', exc)
    raise
