import requests
from decimal import Decimal, ROUND_HALF_UP
from colorama import Fore, Style, init
from datetime import datetime

init(autoreset=True)

def log(message, level="info"):
    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if level == "info":
        print(f"{time_stamp} - {Fore.BLUE}[INFO]{Style.RESET_ALL} {message}")
    elif level == "danger":
        print(f"{time_stamp} - {Fore.RED}[DANGER]{Style.RESET_ALL} {message}")
    elif level == "success":
        print(f"{time_stamp} - {Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")
    elif level == "warning":
        print(f"{time_stamp} - {Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")

def dynamic_round(num, max_decimals=6):
    decimal_num = Decimal(num)
    
    actual_decimals = -decimal_num.as_tuple().exponent
    
    if actual_decimals <= max_decimals:
        return num
    
    quantize_str = '1.' + '0' * max_decimals
    return float(decimal_num.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP))

def get_current_dollar_value():
    try:
        response = requests.get("https://economia.awesomeapi.com.br/json/last/USD")
        response.raise_for_status()
        if response.status_code == 200:
            dollar_value = response.json()["USDBRL"]["bid"]
            return float(dollar_value)
        else:
            return 0
    except Exception as e:
        log(f"Failed to fetch automatic dollar value: {str(e)}", "danger")
        return 0