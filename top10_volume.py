import sys
import os
import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import pandas as pd
from io import StringIO
import time
import threading

st.set_page_config(page_title="Crypto Volume Rankings", page_icon="📊", layout="wide")

# 'src' ディレクトリを sys.path に追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from src.binance_top10 import get_binance_volume_top10
from src.bybit_top10 import get_bybit_volume_top10

# Discord Webhook URLの取得
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    h1 {
        color: black;
    }
    h2 {
        color: black;
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
    }
    h3 {
        color: black;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stDataFrame {
        padding: 0;
        border: none;
    }
    .stDataFrame [data-testid="stTable"] {
        border: none;
    }
    .stDataFrame [data-testid="stTable"] th {
        background-color: #f8f8f8;
        font-weight: bold;
    }
    /* インデックス列（Rank）の幅を調整 */
    [data-testid="stTable"] div[data-testid="column_header"]:first-child,
    [data-testid="stTable"] div[data-testid="cell"]:first-child {
        width: 50px !important;
        min-width: 50px !important;
        max-width: 50px !important;
        flex: 0 0 50px !important;
    }
    .update-time {
        color: #606060;
        font-style: italic;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# キャッシュファイルのパス
CACHE_FILE = "volume_data_cache.json"

def capture_output(func, *args, **kwargs):
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    try:
        func(*args, **kwargs)
    except Exception as e:
        error_message = f"APIリクエストエラー: {str(e)}"
        print(error_message)
        st.error(error_message)  # Streamlitのログにエラーメッセージを表示
    sys.stdout = old_stdout
    return result.getvalue()

def parse_volume_data(data):
    lines = data.strip().split('\n')
    parsed_data = []
    for line in lines:
        if line.startswith(tuple(str(i) for i in range(1, 11))):
            parts = line.split('-')
            rank_symbol = parts[0].strip()
            volume = parts[1].strip().split(':')[1].strip()
            symbol = rank_symbol.split('.')[1].strip()
            rank_part = rank_symbol.split(' ')[0].strip()
            if '.' in rank_part:
                rank = int(rank_part.split('.')[0])
            else:
                rank = int(rank_part)
            parsed_data.append({'Rank': rank, 'Symbol': symbol, 'Volume': volume})
    
    df = pd.DataFrame(parsed_data)
    df = df[['Rank', 'Symbol', 'Volume']]
    return df

def display_volume_data(data, title):
    st.subheader(title)
    parsed_data = parse_volume_data(data)
    st.dataframe(parsed_data, use_container_width=True, hide_index=True)

def save_data_to_cache(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def load_data_from_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return None

def get_next_update_time():
    now = datetime.now(pytz.utc)
    next_update = now.replace(hour=(now.hour // 4) * 4, minute=0, second=0, microsecond=0) + timedelta(hours=4)
    return next_update.strftime("%Y-%m-%d %H:%M:%S UTC")

def send_discord_message(message):
    if not DISCORD_WEBHOOK_URL:
        st.error("Discord Webhook URLが設定されていません。")
        return False

    # メッセージを2000文字以内に分割
    messages = []
    while message:
        if len(message) <= 1900:  # 余裕を持って1900文字で区切る
            messages.append(message)
            break
        # コードブロック(```)の途中で分割しないように調整
        split_index = message[:1900].rfind('\n```\n')
        if split_index == -1:
            split_index = 1900
        messages.append(message[:split_index])
        message = message[split_index:]

    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        for msg_part in messages:
            data = {'content': msg_part}
            response = requests.post(
                DISCORD_WEBHOOK_URL, 
                json=data,
                headers=headers
            )
            if response.status_code != 204:
                print(f"Webhookメッセージ送信に失敗しました。ステータスコード: {response.status_code}")
                print(f"レスポンス内容: {response.text}")
                return False
            time.sleep(1)  # Discord APIのレート制限を考慮して待機
        
        print("Webhookメッセージが正常に送信されました")
        return True
            
    except Exception as e:
        print(f"Webhook送信中にエラーが発生しました: {str(e)}")
        return False

def update_data():
    try:
        # データ取得と整形
        binance_spot = clean_output(capture_output(get_binance_volume_top10, 'spot'))
        binance_futures = clean_output(capture_output(get_binance_volume_top10, 'futures'))
        bybit_spot = clean_output(capture_output(get_bybit_volume_top10, 'spot'))
        bybit_perp = clean_output(capture_output(get_bybit_volume_top10, 'perp'))

        data = {
            'binance_spot': binance_spot,
            'binance_futures': binance_futures,
            'bybit_spot': bybit_spot,
            'bybit_perp': bybit_perp,
            'last_updated': datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        
        save_data_to_cache(data)

        # メッセージを個別に送信
        messages = [
            "**Volume top 10 更新**\n\n**Binance spot:**\n```\n" + binance_spot + "\n```",
            "**Binance perp:**\n```\n" + binance_futures + "\n```",
            "**Bybit spot:**\n```\n" + bybit_spot + "\n```",
            "**Bybit perp:**\n```\n" + bybit_perp + "\n```"
        ]

        for message in messages:
            send_discord_message(message)
            time.sleep(1)  # APIレート制限を考慮

        print("Webhookメッセージを送信しました")

        return data
    except Exception as e:
        error_message = f"データ取得中にエラーが発生しました: {str(e)}"
        print(f"Error: {error_message}")
        send_discord_message(error_message)
        return None

def send_test_notification(data):
    """テスト通知を送信する関数"""
    if not DISCORD_WEBHOOK_URL:
        st.error("Discord Webhook URLが設定されていません。")
        return False

    try:
        current_time = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        test_message = f"""
🔍 **Volume Rankings Test Notification**
Test Time: {current_time}

Binance spot:
```
{data['binance_spot']}
```

Binance perp:
```
{data['binance_futures']}
```

Bybit spot:
```
{data['bybit_spot']}
```

Bybit perp:
```
{data['bybit_perp']}
```"""
        
        return send_discord_message(test_message)
    except Exception as e:
        st.error(f"通知の送信中にエラーが発生しました: {str(e)}")
        return False

def clean_output(output):
    return "\n".join(line.strip() for line in output.strip().split("\n") if line.strip())

def run_app():
    st.title("Trading Volume Rankings")

    data = load_data_from_cache()

    if data is None or (datetime.now(pytz.utc) - datetime.strptime(data['last_updated'], "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=pytz.UTC)) > timedelta(hours=4):
        data = update_data()

    # サイドバーにテスト通知ボタンを追加
    with st.sidebar:
        st.header("通知テスト")
        if st.button("テスト通知を送信"):
            if data and send_test_notification(data):
                st.success("テスト通知が送信されました！")
            else:
                st.error("テスト通知の送信に失敗しました。")

    if data is not None:
        # Binance Section
        st.header("Binance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            display_volume_data(data['binance_spot'], "Spot")
        
        with col2:
            display_volume_data(data['binance_futures'], "Perpetual")

        st.markdown("---")

        # Bybit Section
        st.header("Bybit")
        
        col1, col2 = st.columns(2)
        
        with col1:
            display_volume_data(data['bybit_spot'], "Spot")
        
        with col2:
            display_volume_data(data['bybit_perp'], "Perpetual")

        # 最後の更新時間と次の更新時間を表示
        st.markdown(f"<p class='update-time'>Last updated: {data['last_updated']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='update-time'>Next update: {get_next_update_time()}</p>", unsafe_allow_html=True)
    else:
        st.error("データを取得できませんでした。後でもう一度お試しください。")

    if st.button("データを更新"):
        data = update_data()
        st.experimental_rerun()

def start_periodic_updates():
    while True:
        now = datetime.now(pytz.utc)
        next_update = now.replace(hour=(now.hour // 4) * 4, minute=0, second=0, microsecond=0) + timedelta(hours=4)
        wait_time = (next_update - now).total_seconds()
        time.sleep(wait_time)  # 4時間待つ
        update_data()  # 4時間ごとにデータ更新＆Discord通知

if __name__ == "__main__":
    # 定期更新スレッドの起動
    update_thread = threading.Thread(target=start_periodic_updates, daemon=True)
    update_thread.start()

    run_app()