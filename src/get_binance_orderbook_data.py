import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from datetime import datetime
import os
from binance.client import Client
import pandas as pd

def get_signed_params(secret_key, params):
    query_string = urlencode(params)
    signature = hmac.new(
        secret_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"{query_string}&signature={signature}"

def get_historical_data_link(api_key, secret_key, base_url, symbol, start_time, end_time, data_type):
    endpoint = '/sapi/v1/futures/histDataLink'
    params = {
        'symbol': symbol,
        'startTime': int(start_time.timestamp() * 1000),
        'endTime': int(end_time.timestamp() * 1000),
        'dataType': data_type,
        'timestamp': int(time.time() * 1000)
    }
    query_string = get_signed_params(secret_key, params)
    url = f"{base_url}{endpoint}?{query_string}"
    headers = {'X-MBX-APIKEY': api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def download_file(url, directory="downloads"):
    if not os.path.exists(directory):
        os.makedirs(directory)
    local_filename = url.split('/')[-1].split('?')[0]
    file_path = os.path.join(directory, local_filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return file_path

def get_close_prices(client, symbol, timestamps):
    klines = client.get_historical_klines(
        symbol,
        Client.KLINE_INTERVAL_5MINUTE,
        start_str=timestamps.min().strftime("%d %b %Y %H:%M:%S"),
        end_str=timestamps.max().strftime("%d %b %Y %H:%M:%S")
    )
    price_dict = {}
    for kline in klines:
        timestamp = pd.to_datetime(kline[0], unit='ms', utc=True)
        close_price = float(kline[4])
        price_dict[timestamp] = close_price
    return price_dict
