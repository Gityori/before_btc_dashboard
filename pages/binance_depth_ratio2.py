import os
import sys
import streamlit as st
import requests
import zipfile
import io
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
import traceback

# プロジェクトルートとsrcディレクトリの設定
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from bigquery_integration import upload_dataframe_to_bigquery
from visualizer import create_combined_chart
from binance.client import Client

# 環境変数の設定
API_KEY = os.getenv("BINANCE_API_KEY")
SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
dataset_id = os.getenv("BIGQUERY_DATASET_ID")
table_id = os.getenv("BIGQUERY_TABLE_ID")
service_account_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Binanceクライアントの初期化
client = Client(API_KEY, SECRET_KEY)

def get_latest_available_date():
    """
    利用可能な最新の日付を取得
    Binanceのデータ更新時刻（UTC 8:00 AM）を考慮
    """
    now = datetime.now(pytz.UTC)
    today = now.date()
    current_time = now.time()
    
    # UTC 8:00 AM前の場合、2日前のデータを最新とする
    # UTC 8:00 AM以降の場合、前日のデータを最新とする
    if current_time < datetime.strptime('08:00', '%H:%M').time():
        return today - timedelta(days=2)
    else:
        return today - timedelta(days=1)

def get_btcusdt_price_data(start_time, end_time):
    """
    指定された期間のBTCUSDT価格データを取得
    """
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

def process_depth_data(df):
    """
    5分間隔でデータを処理し、必要な指標を計算
    """
    df['time_group'] = df['timestamp'].dt.floor('5min')
    
    def calculate_metrics(group):
        # 1-3%の範囲のデータ
        data_1_3_percent = group[(group['percentage'].abs() >= 1) & (group['percentage'].abs() <= 3)]
        # 1%以内のデータ
        data_within_1_percent = group[group['percentage'].abs() <= 1]
        # 5%以内のデータ
        data_within_5_percent = group[group['percentage'].abs() <= 5]
        
        # bid/askの計算
        bid_1_3 = data_1_3_percent[data_1_3_percent['percentage'] < 0]['depth'].sum()
        ask_1_3 = data_1_3_percent[data_1_3_percent['percentage'] > 0]['depth'].sum()
        
        return pd.Series({
            'interval_start': group['time_group'].iloc[0],
            'interval_end': group['time_group'].iloc[0] + pd.Timedelta(minutes=5),
            'depth_ratio': bid_1_3 / ask_1_3 if ask_1_3 != 0 else float('inf'),
            'total_qty_1pct': data_within_1_percent['depth'].sum(),
            'total_qty_5pct': data_within_5_percent['depth'].sum()
        })

    results = df.groupby('time_group').apply(calculate_metrics).reset_index(drop=True)
    return results

def download_depth_data(url):
    """
    指定されたURLからデータをダウンロードして処理
    """

    response = requests.get(url)
    
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            csv_filename = zip_ref.namelist()[0]
            with zip_ref.open(csv_filename) as csv_file:
                df = pd.read_csv(csv_file)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # データを処理
                results_df = process_depth_data(df)
                
                return results_df
    else:
        st.error(f"ダウンロードエラー: ステータスコード {response.status_code}")
        return None

def display_utc_time():
    """現在のUTC時刻を表示"""
    now = datetime.now(pytz.UTC)
    return f"現在のUTC時刻: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"

def main():
    st.title("Binance Depth Data Analyzer")
    
    # 現在のUTC時刻を表示
    st.sidebar.write(display_utc_time())
    
    # 初期表示時は最新の利用可能な日付を取得
    latest_date = get_latest_available_date()
    
    # データ更新時刻の説明を表示
    st.sidebar.info("データは通常、UTC 8:00 AMに更新されます。\n"
                    "UTC 8:00 AM以前は2日前までのデータが、\n"
                    "UTC 8:00 AM以降は前日までのデータが利用可能です。")
    
    # 日付選択用のカレンダー
    selected_date = st.date_input(
        "分析する日付を選択してください",
        value=latest_date,
        max_value=latest_date,
        help="利用可能な最新のデータまでを選択できます"
    )
    
    # 選択された日付でURLを構築
    data_url = f"https://data.binance.vision/data/futures/um/daily/bookDepth/BTCUSDT/BTCUSDT-bookDepth-{selected_date}.zip"
    
    # セッション状態の初期化
    if 'last_processed_date' not in st.session_state:
        st.session_state.last_processed_date = None
    
    # 日付が変更されたか、初回表示時の場合にデータを処理
    if selected_date != st.session_state.last_processed_date:
        with st.spinner('データを処理中...'):
            try:
                results_df = download_depth_data(data_url)
                if results_df is not None:
                    # relative_ratio_percentを計算
                    results_df['relative_ratio_percent'] = (results_df['depth_ratio'] - 1) * 100

                    # 価格データの取得と可視化
                    start_time = results_df['interval_start'].min()
                    end_time = results_df['interval_end'].max()
                    price_df = get_btcusdt_price_data(start_time, end_time)

                    fig = create_combined_chart(results_df, price_df)
                    st.plotly_chart(fig, use_container_width=True)

                    # BigQueryへのアップロード
                    try:
                        upload_dataframe_to_bigquery(
                            dataframe=results_df,
                            dataset_id=dataset_id,
                            table_id=table_id,
                            service_account_key_path=service_account_key_path
                        )
                        st.success("データがBigQueryに正常にアップロードされました")
                    except Exception as e:
                        st.error(f"BigQueryへのアップロード中にエラーが発生しました: {str(e)}")
                    
                    # 処理した日付を記録
                    st.session_state.last_processed_date = selected_date
            except Exception as e:
                st.error(f"指定された日付のデータが見つからないか、ダウンロード中にエラーが発生しました: {str(e)}")
                st.write("注意: データは通常、UTC 8:00 AM以降に前日のデータが利用可能になります。")

    # 現在選択されている日付の表示
    st.sidebar.write(f"選択中の日付: {selected_date}")

if __name__ == "__main__":
    main()