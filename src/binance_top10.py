import requests
from operator import itemgetter

def get_exchange_rates():
    # BinanceからUSDTと各通貨の価格を取得
    ticker_url = "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(ticker_url)
    response.raise_for_status()
    data = response.json()

    exchange_rates = {}
    for item in data:
        symbol = item['symbol']
        price = float(item['price'])
        if symbol.endswith('USDT'):
            currency = symbol[:-4]
            exchange_rates[currency] = price
    return exchange_rates

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
                        elif quote_asset in exchange_rates:
                            volume_in_quote = float(item['quoteVolume'])
                            item['volumeUSD'] = volume_in_quote * exchange_rates[quote_asset]
                        elif base_asset in exchange_rates:
                            item['volumeUSD'] = float(item['volume']) * exchange_rates[base_asset]
                        else:
                            item['volumeUSD'] = 0
                    except (ZeroDivisionError, ValueError):
                        item['volumeUSD'] = 0
                else:
                    item['volumeUSD'] = 0
            sorted_data = sorted(data, key=lambda x: float(x.get('volumeUSD', 0)), reverse=True)
            print(f"Binance Spot 取引量トップ10 (USD換算):")
            for i, pair in enumerate(sorted_data[:10], 1):
                symbol = pair['symbol']
                volume_usd = pair.get('volumeUSD', 0)
                print(f"{i}. {symbol:<10} - 取引量: ${volume_usd:,.2f}")
        else:  # futures
            usdt_data = get_binance_futures_data(usdt_ticker_url)
            coin_data = get_binance_futures_data(coin_ticker_url)

            data = []
            # USDT建て先物の処理
            for item in usdt_data:
                if is_perpetual(item['symbol']):
                    item['volumeUSD'] = float(item['quoteVolume'])
                    item['type'] = 'USDT-Margined'
                    data.append(item)

            # コイン建て先物の処理
            for item in coin_data:
                if is_perpetual(item['symbol']):
                    # 契約サイズを決定
                    if item['symbol'].startswith('BTCUSD'):
                        contract_size = 100  # BTCUSDの契約サイズは100 USD
                    else:
                        contract_size = 10   # 他の通貨ペアは10 USD

                    # 取引量を計算
                    item['volumeUSD'] = float(item['volume']) * contract_size
                    item['type'] = 'COIN-Margined'
                    data.append(item)

            sorted_data = sorted(data, key=lambda x: float(x.get('volumeUSD', 0)), reverse=True)
            print(f"Binance Futures 取引量トップ10 (USD換算):")
            for i, pair in enumerate(sorted_data[:10], 1):
                symbol = pair['symbol']
                volume_usd = float(pair.get('volumeUSD', 0))
                contract_type = pair['type']
                print(f"{i}. {symbol:<15} - 取引量: ${volume_usd:,.2f} ({contract_type})")

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
