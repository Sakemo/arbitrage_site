import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.scrap import _betfair_certlogin_request

try:
    token = _betfair_certlogin_request()
    print('✅ Direct certlogin success!')
    print('Session token:', token)
except Exception as exc:
    print('❌ Direct certlogin failed:', exc)
    raise
