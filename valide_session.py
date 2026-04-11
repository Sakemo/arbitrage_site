import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

USERNAME = os.getenv("BETFAIR_USERNAME")
PASSWORD = os.getenv("BETFAIR_PASSWORD")
APP_KEY = os.getenv("BETFAIR_APP_KEY")

if not USERNAME or not PASSWORD or not APP_KEY:
    missing_vars = [
        name
        for name, value in (
            ("BETFAIR_USERNAME", USERNAME),
            ("BETFAIR_PASSWORD", PASSWORD),
            ("BETFAIR_APP_KEY", APP_KEY),
        )
        if not value
    ]
    raise RuntimeError(f"Variaveis ausentes no ambiente/.env: {', '.join(missing_vars)}")

payload = {"username": USERNAME, "password": PASSWORD}
headers = {
    "X-Application": APP_KEY,
    "Content-Type": "application/x-www-form-urlencoded",
}
cert_file = BASE_DIR / "certs" / "client-2048.crt"
key_file = BASE_DIR / "certs" / "client-2048.key"

try:
    resp = requests.post(
        "https://identitysso-cert.betfair.bet.br/api/certlogin",
        data=payload,
        cert=(str(cert_file), str(key_file)),
        headers=headers,
        timeout=30,
    )
    print(f"HTTP {resp.status_code}")
    print(resp.text)

    if resp.ok:
        resp_json = resp.json()
        print(resp_json.get("loginStatus"))
        print(resp_json.get("sessionToken"))
except requests.RequestException as exc:
    print(f"Request failed: {exc}")
