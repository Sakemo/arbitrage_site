import os
import requests
from modules.scrap import _betfair_certlogin_request

def main():
    token = _betfair_certlogin_request()
    print('token', token[:10] + '...')
    headers = {
        'X-Application': os.getenv('BETFAIR_APP_KEY'),
        'X-Authentication': token,
        'Content-Type': 'application/json',
    }
    catalogue_url = 'https://api.betfair.bet.br/exchange/betting/rest/v1.0/listMarketCatalogue/'
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
    resp = requests.post(catalogue_url, json=payload, headers=headers, timeout=30)
    print('catalogue status', resp.status_code)
    print(resp.text[:1000])
    if resp.status_code != 200:
        return
    catalog = resp.json()
    market_ids = [item['marketId'] for item in catalog[:5]]
    print('market ids', market_ids)

    for price_data in [['EX_ALL_OFFERS'], ['EX_BEST_OFFERS'], ['EX_TRADED']]:
        book_url = 'https://api.betfair.bet.br/exchange/betting/rest/v1.0/listMarketBook/'
        payload2 = {
            'marketIds': market_ids,
            'priceProjection': {'priceData': price_data},
        }
        print('Testing priceData', price_data)
        resp2 = requests.post(book_url, json=payload2, headers=headers, timeout=30)
        print('status', resp2.status_code)
        print(resp2.text[:2000])

if __name__ == '__main__':
    main()
