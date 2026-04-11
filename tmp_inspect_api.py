import inspect
from betfairlightweight import APIClient

print('APIClient signature:', inspect.signature(APIClient))
print('APIClient dir:', [name for name in dir(APIClient) if 'session' in name.lower() or 'login' in name.lower()])
print('APIClient init source:')
try:
    print(inspect.getsource(APIClient.__init__))
except Exception as e:
    print('source error', e)
