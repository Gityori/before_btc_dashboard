import os
import sys
import streamlit as st

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from get_binance_orderbook_data import get_historical_data_link, download_file, get_close_prices
from calculate_depth import process_large_file
from visualizer import create_combined_chart

import logging
import traceback
from datetime import datetime, timedelta
import time
import pytz
import pandas as pd
from binance.client import Client

# Binance APIクレデンシャル
API_KEY = os.getenv["BINANCE_API_KEY"]
SECRET_KEY = os.getenv["BINANCE_SECRET_KEY"]

# Binance APIベースURL
BASE_URL = 'https://api.binance.com'

# Binanceクライアントの初期化
client = Client(API_KEY, SECRET_KEY)

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_latest_available_date_utc():
    utc_now = datetime.now(pytz.UTC)
    utc_time = utc_now.time()
    comparison_time = datetime.strptime('08:00:00', '%H:%M:%S').time()
    is_before_8am = utc_time < comparison_time
    latest_date = (utc_now - timedelta(days=2)).date() if is_before_8am else (utc_now - timedelta(days=1)).date()
    return latest_date

def run_data_processing():
    symbol = "BTCUSDT"
    data_type = "S_DEPTH"

    latest_date = get_latest_available_date_utc()
    print(f"Latest available date: {latest_date}")
    end_time = datetime.combine(latest_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
    start_time = end_time - timedelta(days=1)

    print(f"Requesting data for {symbol}")
    print(f"Start Time: {start_time}")
    print(f"End Time: {end_time}")
    print(f"Data Type: {data_type}")

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        data_link_response = get_historical_data_link(API_KEY, SECRET_KEY, BASE_URL, symbol, start_time, end_time, data_type)
        
        if data_link_response and 'data' in data_link_response and data_link_response['data']:
            download_link = data_link_response['data'][0]['url']
            
            try:
                file_path = download_file(download_link)
                print(f"File downloaded to: {file_path}")
                # データ処理
                start_processing_time = time.time()
                results_df = process_large_file(
                    file_path, 
                    start_time=start_time, 
                    end_time=end_time, 
                    get_close_prices_func=lambda timestamps: get_close_prices(client, symbol, timestamps)
                )
                processing_time = time.time() - start_processing_time
                print(f"Data processing completed in {processing_time:.2f} seconds")
                
                if not results_df.empty:
                    print("\nData processed successfully")
                    if results_df['interval_end'].iloc[-1] > end_time:
                        results_df = results_df[:-1]
                    print(f"Total rows: {len(results_df)}")
                    
                    return results_df
                else:
                    print("Failed to process the file or no data in the specified time range")
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                print("Traceback:")
                traceback.print_exc()
        else:
            print(f"Failed to obtain download link for date {end_time.date()}")
        
        retry_count += 1
        if retry_count < max_retries:
            print(f"Retrying with previous day's data. Attempt {retry_count + 1} of {max_retries}")
            end_time -= timedelta(days=1)
            start_time -= timedelta(days=1)
        else:
            print("Maximum retries reached. Unable to fetch data.")
    
    return None

def get_btcusdt_price_data(start_time, end_time):
    klines = client.get_historical_klines(
        "BTCUSDT", 
        Client.KLINE_INTERVAL_5MINUTE, 
        start_time.strftime("%d %b %Y %H:%M:%S"), 
        end_time.strftime("%d %b %Y %H:%M:%S")
    )
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'quote_asset_volume', 'number_of_trades', 
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    return df[['timestamp', 'close']]

def main():
    st.header("Binance Depth Ratio and BTCUSDT Price")
    
    if st.button("Run Data Processing"):
        with st.spinner('Processing data... This may take a few minutes.'):
            results_df = run_data_processing()
        
        if results_df is not None:
            # BTCUSDTの価格データを取得
            start_time = results_df['interval_start'].min()
            end_time = results_df['interval_end'].max()
            price_df = get_btcusdt_price_data(start_time, end_time)
            
            # グラフの作成
            fig = create_combined_chart(results_df, price_df)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Failed to process data. Please check the logs for more information.")

if __name__ == "__main__":
    main()
