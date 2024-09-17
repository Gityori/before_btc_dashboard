import requests
from decimal import Decimal

def is_perpetual(symbol):
    return not any(char.isdigit() for char in symbol)

def get_bybit_volume_top10(category='spot'):
    base_url = "https://api.bybit.com"
    endpoint = "/v5/market/tickers"
    
    if category not in ['spot', 'perp']:
        raise ValueError("Invalid category. Choose 'spot' or 'perp'")

    try:
        categories = ['linear', 'inverse'] if category == 'perp' else [category]
        all_tickers = []

        for cat in categories:
            params = {'category': cat}
            response = requests.get(f"{base_url}{endpoint}", params=params)
            data = response.json()

            if data['retCode'] != 0:
                raise Exception(f"API error: {data['retMsg']}")

            tickers = data['result']['list']
            all_tickers.extend(tickers)

        # 取引量をUSD価値に変換
        for ticker in all_tickers:
            symbol = ticker['symbol']
            volume = Decimal(ticker['volume24h'])
            last_price = Decimal(ticker['lastPrice'])

            # インバース無期限契約の処理
            if category == 'perp' and symbol.endswith('USD') and is_perpetual(symbol):
                usd_volume = volume
            else:
                # デノミネーションの修正
                if symbol.startswith(('1000', '10000')):
                    denominator = 1000 if symbol.startswith('1000') else 10000
                    volume = volume / denominator
                    last_price = last_price * denominator

                # USD価値の計算
                if symbol.endswith(('USDT', 'USDC', 'USD')):
                    usd_volume = volume * last_price
                elif symbol.endswith('BTC'):
                    btc_price = next((Decimal(t['lastPrice']) for t in all_tickers if t['symbol'] == 'BTCUSDT'), None)
                    if btc_price:
                        usd_volume = volume * btc_price * last_price
                    else:
                        usd_volume = volume * last_price  # Fallback if BTCUSDT pair is not found
                else:
                    usd_volume = volume * last_price

            ticker['usd_volume'] = usd_volume

        # 無期限取引のみをフィルタリング（perp カテゴリーの場合）
        if category == 'perp':
            all_tickers = [t for t in all_tickers if is_perpetual(t['symbol'])]

        # USD取引量でソート
        sorted_tickers = sorted(all_tickers, key=lambda x: x['usd_volume'], reverse=True)

        print(f"Bybit {category.capitalize()} 取引量トップ10 (USD換算):")
        for i, ticker in enumerate(sorted_tickers[:10], 1):
            symbol = ticker['symbol']
            usd_volume = ticker['usd_volume']
            
            print(f"{i}. {symbol:<12} - 取引量: ${usd_volume:,.2f}")

    except requests.RequestException as e:
        print(f"APIリクエストエラー: {e}")
    except (KeyError, ValueError, Exception) as e:
        print(f"データ処理エラー: {e}")

if __name__ == "__main__":
    print("Bybitスポット取引のトップ10:")
    get_bybit_volume_top10('spot')
    print("Bybit無期限取引のトップ10:")
    get_bybit_volume_top10('perp')