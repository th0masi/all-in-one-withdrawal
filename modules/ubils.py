import math
import random
import time
import ccxt
import requests

from _decimal import Decimal
from config import api_info


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except ccxt.errors.AuthenticationError as e:
            error_message = str(e)
            exchange = args[0] if args else ""
            if "Request IP not in whitelist" in error_message:
                print(f"\n>>>  Error: Your IP address is not in the whitelist ")
            else:
                print(f"\n>>>  Error: Invalid API Key, secret or password. Please check the "
                      f"'apiKey'/'secret'/'password' value in config.py file")
                print(f"     Original Error: {error_message}")
            return False

        except ccxt.errors.NetworkError as e:
            error_message = str(e)
            if "ProxyError" in error_message:
                print("\n>>>  Error: Unable to connect to the proxy.")
                print(f"     Original Error: {error_message}")
            elif "NameResolutionError" in error_message:
                print(f"\n>>>  Error: Failed to resolve the host name.")
                print(f"     Original Error: {error_message}")
            else:
                print(f"\n>>>  Unhandled network error: {error_message}")
                print(f"     Original Error: {error_message}")
            return False

        except Exception as e:
            error_message = str(e)
            if "kucoin account.available.amount" in error_message:
                print("\n>>>  Error: Error: You need to enable the Withdraw to API Address Book option (Адреса Вывода, Применяемые к Выводу API): https://www.kucoin.com/withdraw-addr-manage")
            print(f"\n>>>  Unexpected error: {error_message}")
            return False

    return wrapper


@handle_exceptions
def get_ccxt(exchange_name):
    exchange_config = api_info[exchange_name]
    exchange_options = {
        'apiKey': exchange_config['apiKey'],
        'secret': exchange_config['secret'],
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
        }
    }

    if 'password' in exchange_config:
        exchange_options['password'] = exchange_config['password']

    if exchange_config.get('proxy_url'):
        exchange_options['proxies'] = {
            'http': exchange_config['proxy_url'],
            'https': exchange_config['proxy_url'],
        }

    exchange_class = getattr(ccxt, exchange_name)
    exchange = exchange_class(exchange_options)

    return exchange


@handle_exceptions
def okx_get_withdrawal_info(token):
        exchange = get_ccxt("okx")
        currencies = exchange.fetch_currencies()

        networks = []
        network_data = {}

        if currencies is not None:
            for currency_code, currency in currencies.items():
                if currency_code == token.upper():
                    networks_info = currency.get('networks')
                    if networks_info is not None:
                        for network, network_info in networks_info.items():

                            fee = network_info.get('fee')
                            if fee is not None:
                                fee = float(fee)
                                fee = smart_round(fee)

                            min_withdrawal = network_info.get('limits', {}).get('withdraw', {}).get('min')
                            if min_withdrawal is not None:
                                min_withdrawal = float(min_withdrawal)

                            id = network_info.get('id')
                            is_withdraw_enabled = network_info.get('withdraw', False)

                            if is_withdraw_enabled:
                                network_data[network] = (id, fee, min_withdrawal)
                                networks.append(network)
                    else:
                        print(f"\n>>>  Currency {currency_code} doesn't contain 'networks' attribute")
        else:
            print("\n>>>  Currencies not found")

        return networks, network_data


@handle_exceptions
def okx_withdraw(address, amount, token_name, network, fee):
    exchange = get_ccxt("okx")
    network_name = network.split("-")[1]

    exchange.withdraw(token_name, amount, address,
                      params={
                          "chainName": network,
                          "fee": fee,
                          "pwd": '-',
                          "amt": amount,
                          "network": network_name,
                      }
                      )

    print(f'\n>>>  [OKX] Successfully withdrawn {amount} {token_name} ', flush=True)
    print(f'     {address}', flush=True)
    return True


@handle_exceptions
def binance_get_withdrawal_info(token):
    exchange = get_ccxt("binance")
    currencies = exchange.fetch_currencies()

    networks = []
    network_data = {}

    if currencies is not None:
        for currency_code, currency in currencies.items():
            if currency_code == token.upper():
                try:
                    network_list = currency.get('info', {}).get('networkList', [])
                    for network in network_list:
                        is_withdraw_enabled = network.get('withdrawEnable', False)

                        fee = network.get('withdrawFee')
                        if fee is not None:
                            fee = float(fee)
                            fee = smart_round(fee)

                        min_withdrawal = network.get('withdrawMin')
                        if min_withdrawal is not None:
                            min_withdrawal = float(min_withdrawal)

                        network_name = network.get('name', '')
                        network_code = network.get('network', '')

                        if is_withdraw_enabled:
                            network_data[network_name] = (network_code, fee, min_withdrawal)
                            networks.append(network_name)
                except Exception as e:
                    print(f"\n>>>  Error fetching fees for {currency_code}: {str(e)}")
                break
    else:
        print("\n>>>  Currencies not found")

    return networks, network_data


@handle_exceptions
def binance_withdraw(address, amount, token_name, network):
    exchange = get_ccxt("binance")

    exchange.withdraw(
        code=token_name,
        amount=amount,
        address=address,
        tag=None,
        params={
            "network": network
        }
    )
    print(f'\n>>>  [Binance] Successfully withdrawn {amount} {token_name} ', flush=True)
    print(f'     {address}', flush=True)
    return True


@handle_exceptions
def kucoin_get_withdrawal_info(token):
    exchange = get_ccxt("kucoin")
    currencies = exchange.fetch_currencies()

    networks = []
    network_data = {}

    if currencies is not None:
        for currency_code, currency in currencies.items():
            if currency_code == token.upper():
                try:
                    for network_code, network in currency['networks'].items():
                        is_withdraw_enabled = network.get('info', {}).get('isWithdrawEnabled', 'false') == 'true'

                        fee = network.get('fee')
                        if fee is not None:
                            fee = float(fee)
                            fee = smart_round(fee)

                        min_withdrawal = network.get('info', {}).get('withdrawMinSize')
                        if min_withdrawal is not None:
                            min_withdrawal = float(min_withdrawal)

                        chain_full_name = network.get('info', {}).get('chainFullName', '')
                        if is_withdraw_enabled:
                            network_data[chain_full_name] = (network_code, fee, min_withdrawal)
                            networks.append(chain_full_name)
                except Exception as e:
                    print(f"\n>>>  Error fetching fees for {currency_code}: {str(e)}")
                break
    else:
        print("\n>>>  Currencies not found")

    return networks, network_data


@handle_exceptions
def kucoin_withdraw(address, amount, token_name, network):
    exchange = get_ccxt("kucoin")

    exchange.withdraw(
        code=token_name,
        amount=amount,
        address=address,
        params={
            "network": network
        }
    )
    print(f'\n>>>  [Kucoin] Successfully withdrawn {amount} {token_name} ', flush=True)
    print(f'     {address}', flush=True)
    return True


@handle_exceptions
def mexc_get_withdrawal_info(token):
    exchange = get_ccxt("mexc")
    currencies = exchange.fetch_currencies()

    networks = []
    network_data = {}

    if currencies is not None:
        for currency_code, currency in currencies.items():
            if currency_code == token.upper():
                try:
                    network_list = currency.get('info', {}).get('networkList', [])
                    for network in network_list:
                        is_withdraw_enabled = network.get('withdrawEnable', False)

                        fee = network.get('withdrawFee')
                        if fee is not None:
                            fee = float(fee)
                            fee = smart_round(fee)

                        min_withdrawal = network.get('withdrawMin')
                        if min_withdrawal is not None:
                            min_withdrawal = float(min_withdrawal)

                        network_name = network.get('network', '')
                        if fee is not None and is_withdraw_enabled:
                            network_data[network_name] = (network_name, fee, min_withdrawal)
                            networks.append(network_name)
                except Exception as e:
                    print(f"\n>>>  Error fetching fees for {currency_code}: {str(e)}")
                break
    else:
        print("\n>>>  Currencies not found")

    return networks, network_data


@handle_exceptions
def mexc_withdraw(address, amount, token_name, network):
    exchange = get_ccxt("mexc")

    exchange.withdraw(
        code=token_name,
        amount=amount,
        address=address,
        params={
            "network": network
        }
    )
    print(f'\n>>>  [Mexc] Successfully withdrawn {amount} {token_name} ', flush=True)
    print(f'     {address}', flush=True)
    return True


@handle_exceptions
def gate_get_withdrawal_info(token):
    exchange = get_ccxt("gate")
    currencies = exchange.fetch_currencies()

    networks = []
    network_data = {}

    if currencies is not None:
        for currency_code, currency in currencies.items():
            if currency_code == token.upper():
                try:
                    networks_info = currency.get('networks', {})
                    for network_id, network_info in networks_info.items():
                        is_withdraw_enabled = network_info.get('withdraw', False)

                        fee = network_info.get('fee')
                        if fee is not None:
                            fee = float(fee)
                            fee = smart_round(fee)

                        min_withdrawal = network_info.get('minWithdrawAmt')
                        if min_withdrawal is not None:
                            min_withdrawal = float(min_withdrawal)

                        network_name = network_info.get('network', '')
                        if is_withdraw_enabled:
                            network_data[network_name] = (network_id, fee, min_withdrawal)
                            networks.append(network_name)

                except Exception as e:
                    print(f"\n>>>  Error fetching fees for {currency_code}: {str(e)}")
                break
    else:
        print("\n>>>  Currencies not found")

    return networks, network_data


@handle_exceptions
def gate_withdraw(address, amount, token_name, network):
    exchange = get_ccxt("gate")

    exchange.withdraw(
        code=token_name,
        amount=amount,
        address=address,
        params={
            "network": network
        }
    )
    print(f'\n>>>  [Gate] Successfully withdrawn {amount} {token_name} ', flush=True)
    print(f'     {address}', flush=True)
    return True


@handle_exceptions
def huobi_get_withdrawal_info(token):
    exchange = get_ccxt("huobi")
    currencies = exchange.fetch_currencies()

    networks = []
    network_data = {}

    if currencies is not None:
        for currency_code, currency in currencies.items():
            if currency_code == token.upper():
                try:
                    chains_info = currency.get('info', {}).get('chains', [])
                    for chain_info in chains_info:
                        is_withdraw_enabled = chain_info.get('withdrawStatus', 'prohibited') == 'allowed'

                        fee = chain_info.get('transactFeeWithdraw')
                        if fee is not None:
                            fee = float(fee)
                            fee = smart_round(fee)

                        min_withdrawal = chain_info.get('minWithdrawAmt')
                        if min_withdrawal is not None:
                            min_withdrawal = float(min_withdrawal)

                        chain_name = chain_info.get('displayName', '')
                        if is_withdraw_enabled:
                            network_data[chain_name] = (chain_name, fee, min_withdrawal)
                            networks.append(chain_name)
                except Exception as e:
                    print(f"\n>>>  Error fetching fees for {currency_code}: {str(e)}")
                break
    else:
        print("\n>>>  Currencies not found")

    return networks, network_data


@handle_exceptions
def huobi_withdraw(address, amount, token_name, network):
    exchange = get_ccxt("huobi")

    exchange.withdraw(
        code=token_name,
        amount=amount,
        address=address,
        params={
            "network": network
        }
    )
    print(f'\n>>>  [Huobi] Successfully withdrawn {amount} {token_name} ', flush=True)
    print(f'     {address}', flush=True)
    return True


@handle_exceptions
def bitget_get_withdrawal_info(token):
    exchange = get_ccxt("bitget")
    currencies = exchange.fetch_currencies()

    networks = []
    network_data = {}

    if currencies is not None:
        for currency_code, currency in currencies.items():
            if currency_code == token.upper():
                try:
                    chains_info = currency.get('info', {}).get('chains', [])
                    for chain_info in chains_info:
                        is_withdraw_enabled = chain_info.get('withdrawable', 'false') == 'true'

                        fee = chain_info.get('withdrawFee')
                        if fee is not None:
                            fee = float(fee)
                            fee = smart_round(fee)

                        min_withdrawal = chain_info.get('minWithdrawAmount')
                        if min_withdrawal is not None:
                            min_withdrawal = float(min_withdrawal)

                        chain_name = chain_info.get('chain', '')

                        if chain_name == 'ETH':
                            chain_name = 'ERC20'
                            
                        if is_withdraw_enabled:
                            network_data[chain_name] = (chain_name, fee, min_withdrawal)
                            networks.append(chain_name)
                except Exception as e:
                    print(f"\n>>>  Error fetching fees for {currency_code}: {str(e)}")
                break
    else:
        print("\n>>>  Currencies not found")

    return networks, network_data


@handle_exceptions
def bitget_withdraw(address, amount, token_name, network):
    exchange = get_ccxt("bitget")

    exchange.withdraw(
        code=token_name,
        amount=amount,
        address=address,
        params={
            "network": network
        }
    )
    print(f'\n>>>  [BitGet] Successfully withdrawn {amount} {token_name} ', flush=True)
    print(f'     {address}', flush=True)
    return True


def is_proxy_alive(proxy_url):
    if not proxy_url:
        return None  # Пропускаем, если proxy_url пустой

    try:
        response = requests.get('https://google.com', proxies={'http': proxy_url, 'https': proxy_url}, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        return False


def check_proxies():
    for api, api_details in api_info.items():
        proxy_status = is_proxy_alive(api_details['proxy_url'])
        if proxy_status is None:
            continue
        if proxy_status:
            print(f"Proxy for {api} is working correctly.")
        else:
            print(f"Proxy for {api} is not working."
                  "You should check the proxy type (SOCKS5 or HTTPS) and verify the credentials.")


def smart_round(number):
    if isinstance(number, (int, float, Decimal)):
        abs_num = abs(number)
        if abs_num == 0:
            return 0
        elif abs_num >= 1:
            return round(number, 2)
        elif 0 < abs_num < 1e-4:
            return "{:.8f}".format(number)
        else:
            return round(number, 3 - int(math.floor(math.log10(abs_num)) + 1))
    else:
        raise ValueError("    Функция принимает только числа (целые и с плавающей точкой) [function smart_round]")
