import os
import sys
import streamlit as st

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from datetime import datetime, timedelta
import time
from binance.client import Client

from calculate_heatmap import process_data
from fetch_Kline_data import get_binance_data
from src.visualizer import create_weekday_plot, create_hourly_plot, create_heatmap

def main():
    st.title('BINANCE BTCUSDT SPOT ANALYSIS')

    # Binance API setup
    API_KEY = os.getenv("BINANCE_API_KEY")
    SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
    client = Client(API_KEY, SECRET_KEY)

    # セッション状態の初期化
    if 'auto_update' not in st.session_state:
        st.session_state.auto_update = True  # デフォルトでオン
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None

    # データ取得と表示関数
    def fetch_and_display_data():
        end_time = datetime.now()
        start_time = end_time - timedelta(days=90)
        data = get_binance_data(client, 'BTCUSDT', Client.KLINE_INTERVAL_1HOUR, start_time, end_time)

        if data.empty:
            st.warning("データが取得できませんでした。")
            return

        # データ処理
        weekday_return, hour_return, heatmap_data = process_data(data)

        # グラフを横に並べて表示
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_weekday_plot(weekday_return), use_container_width=True)
        with col2:
            st.plotly_chart(create_hourly_plot(hour_return), use_container_width=True)

        # ヒートマップの表示
        st.plotly_chart(create_heatmap(heatmap_data), use_container_width=True)

        st.session_state.last_update = datetime.now()

    # 初回データ取得と表示
    fetch_and_display_data()

    # 自動更新のオン/オフトグルと最終更新時刻の表示
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.auto_update = st.toggle("自動更新", value=st.session_state.auto_update)
    with col2:
        if st.session_state.last_update:
            st.text(f"最終更新: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

    # 次の更新時刻を計算
    now = datetime.now()
    next_update = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    time_to_next_update = (next_update - now).total_seconds()

    # 自動更新ロジック
    if st.session_state.auto_update:
        time.sleep(time_to_next_update)
        st.experimental_rerun()

if __name__ == "__main__":
    main()