import requests
import json
from operator import itemgetter

def get_exchange_rates():
    url = "https://api.coingecko.com/api/v3/exchange_rates"
    response = requests.get(url)
    response.raise_for_status()  # ステータスコードがエラーの場合、例外を発生させる
    data = response.json()
    
    btc_usd_rate = data['rates']['usd']['value']
    
    usd_rates = {}
    for currency, rate_data in data['rates'].items():
        if currency != 'usd':
            usd_rates[currency] = btc_usd_rate / rate_data['value']
    
    return usd_rates

def get_binance_futures_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"APIリクエストエラー: {e}")
        if response is not None:
            print(f"ステータスコード: {response.status_code}")
            print(f"レスポンス内容: {response.text}")
        return []

def is_perpetual(symbol):
    return symbol.endswith('PERP') or (not any(char.isdigit() for char in symbol))

def get_binance_volume_top10(trade_type='spot'):
    if trade_type == 'spot':
        ticker_url = "https://api.binance.com/api/v3/ticker/24hr"
        exchange_info_url = "https://api.binance.com/api/v3/exchangeInfo"
    elif trade_type == 'futures':
        usdt_ticker_url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        coin_ticker_url = "https://dapi.binance.com/dapi/v1/ticker/24hr"
    else:
        raise ValueError("Invalid trade type. Choose 'spot' or 'futures'.")

    try:
        exchange_rates = get_exchange_rates()
        
        if trade_type == 'spot':
            exchange_info_response = requests.get(exchange_info_url)
            exchange_info_response.raise_for_status()
            exchange_info = exchange_info_response.json()
            symbols_info = {s['symbol']: s for s in exchange_info['symbols']}

            response = requests.get(ticker_url)
            response.raise_for_status()
            data = response.json()

            usdt_prices = {item['symbol'][:-4]: float(item['lastPrice']) for item in data if item['symbol'].endswith('USDT')}

            for item in data:
                symbol = item['symbol']
                if symbol in symbols_info:
                    base_asset = symbols_info[symbol]['baseAsset']
                    quote_asset = symbols_info[symbol]['quoteAsset']
                    
                    try:
                        if quote_asset == 'USDT':
                            item['volumeUSD'] = float(item['quoteVolume'])
                        elif base_asset == 'USDT':
                            item['volumeUSD'] = float(item['volume'])
                        elif quote_asset.lower() in exchange_rates:
                            volume_in_quote = float(item['quoteVolume'])
                            item['volumeUSD'] = volume_in_quote * exchange_rates[quote_asset.lower()]
                        elif base_asset in usdt_prices:
                            item['volumeUSD'] = float(item['volume']) * usdt_prices[base_asset]
                        else:
                            item['volumeUSD'] = 0
                    except (ZeroDivisionError, ValueError):
                        item['volumeUSD'] = 0
                else:
                    item['volumeUSD'] = 0
        else:  # futures
            usdt_data = get_binance_futures_data(usdt_ticker_url)
            coin_data = get_binance_futures_data(coin_ticker_url)

            data = []
            for item in usdt_data:
                if is_perpetual(item['symbol']):
                    item['volumeUSD'] = float(item['volume']) * float(item['lastPrice'])
                    item['type'] = 'USDT-Margined'
                    data.append(item)

            for item in coin_data:
                if is_perpetual(item['symbol']):
                    contract_size = 100 if item['symbol'].startswith('BTC') else 10
                    item['volumeUSD'] = float(item['volume']) * contract_size
                    item['type'] = 'COIN-Margined'
                    data.append(item)

        sorted_data = sorted(data, key=lambda x: float(x.get('volumeUSD', 0)), reverse=True)

        print(f"Binance{' 先物' if trade_type == 'futures' else ''} 取引量トップ10 (USD換算):")
        for i, pair in enumerate(sorted_data[:10], 1):
            symbol = pair['symbol']
            volume_usd = pair.get('volumeUSD', 0)
            
            if trade_type == 'futures':
                contract_type = pair['type']
                print(f"{i}. {symbol:<15} - 取引量: ${volume_usd:,.2f}")
            else:
                print(f"{i}. {symbol:<10} - 取引量: ${volume_usd:,.2f}")

    except requests.RequestException as e:
        print(f"APIリクエストエラー: {e}")
        if e.response is not None:
            print(f"ステータスコード: {e.response.status_code}")
            print(f"レスポンス内容: {e.response.text}")
    except (KeyError, ValueError) as e:
        print(f"データ処理エラー: {e}")

if __name__ == "__main__":
    print("スポット取引のトップ10:")
    get_binance_volume_top10('spot')
    print("先物取引のトップ10:")
    get_binance_volume_top10('futures')
