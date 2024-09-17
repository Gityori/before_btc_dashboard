from binance.client import Client
import pandas as pd
from datetime import datetime, timedelta
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_binance_data(client: Client, symbol: str, interval: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Fetch historical klines data from Binance API.
    
    :param client: Binance API client
    :param symbol: Trading symbol (e.g., 'BTCUSDT')
    :param interval: Kline interval (e.g., Client.KLINE_INTERVAL_1HOUR)
    :param start_time: Start time for data fetch
    :param end_time: End time for data fetch
    :return: DataFrame containing the fetched data
    """
    try:
        klines = client.get_historical_klines(symbol, interval, start_time.strftime('%d %b %Y %H:%M:%S'), end_time.strftime('%d %b %Y %H:%M:%S'))
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        data.set_index('timestamp', inplace=True)
        data['close'] = data['close'].astype(float)
        return data
    except Exception as e:
        logging.error(f"Error fetching data from Binance API: {e}")
        return pd.DataFrame()
