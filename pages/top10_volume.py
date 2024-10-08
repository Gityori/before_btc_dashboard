import sys
import os
import streamlit as st

st.set_page_config(page_title="Crypto Volume Rankings", page_icon="📊", layout="wide")

# 'src' ディレクトリを sys.path に追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

import binance_top10
import bybit_top10

# 以降、binance_top10 や bybit_top10 の関数を使用します
binance_spot = binance_top10.get_binance_volume_top10('spot')
bybit_spot = bybit_top10.get_bybit_volume_top10('spot')
# 他の必要なインポート
from datetime import datetime, timedelta
import pytz
import json
import asyncio
import pandas as pd
import discord
from io import StringIO

# Discord設定
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

# Discordクライアントの初期化
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# カスタムCSS
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
            rank = rank_symbol.split('.')[0]
            symbol = rank_symbol.split('.')[1].strip()
            parsed_data.append({'Rank': rank, 'Symbol': symbol, 'Volume': volume})
    return pd.DataFrame(parsed_data)

def display_volume_data(data, title):
    st.subheader(title)
    parsed_data = parse_volume_data(data)
    parsed_data.reset_index(drop=True, inplace=True)  # インデックスをリセット
    st.dataframe(parsed_data, use_container_width=True)

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

async def send_discord_message(message):
    if client.is_ready():
        channel = client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send(message)
        else:
            print(f"Error: Channel with ID {DISCORD_CHANNEL_ID} not found.")
    else:
        print("Error: Discord client is not ready.")

def clean_output(output):
    # 先頭と末尾の空白行を削除し、各行の余分な空白を削除
    return "\n".join(line.strip() for line in output.strip().split("\n") if line.strip())

async def update_data():
    try:
        # データ取得と整形
        st.write("Fetching Binance spot data...")
        binance_spot = clean_output(capture_output(binance_top10.get_binance_volume_top10, 'spot'))
        st.write(f"Binance spot data: {binance_spot}")

        st.write("Fetching Binance futures data...")
        binance_futures = clean_output(capture_output(binance_top10.get_binance_volume_top10, 'futures'))
        st.write(f"Binance futures data: {binance_futures}")

        st.write("Fetching Bybit spot data...")
        bybit_spot = clean_output(capture_output(bybit_top10.get_bybit_volume_top10, 'spot'))
        st.write(f"Bybit spot data: {bybit_spot}")

        st.write("Fetching Bybit perpetual data...")
        bybit_perp = clean_output(capture_output(bybit_top10.get_bybit_volume_top10, 'perp'))
        st.write(f"Bybit perpetual data: {bybit_perp}")

        data = {
            'binance_spot': binance_spot,
            'binance_futures': binance_futures,
            'bybit_spot': bybit_spot,
            'bybit_perp': bybit_perp,  # ここを変更
            'last_updated': datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        
        save_data_to_cache(data)

        # 1つのメッセージとして送信
        message = f"""

Volume top 10 更新

Binance spot:
```
{binance_spot}
```

Binance perp:
```
{binance_futures}
```

Bybit spot:
```
{bybit_spot}
```

Bybit perp:
```
{bybit_perp}
```"""

        await send_discord_message(message)
        print("Message sent successfully!")

        return data
    except Exception as e:
        error_message = f"データ取得中にエラーが発生しました: {str(e)}"
        print(f"Error: {error_message}")
        await send_discord_message(error_message)
        return None


async def run_app():
    await client.wait_until_ready()
    print(f'{client.user} has connected to Discord!')
        
    st.title("Trading Volume Rankings")

    if 'first_run' not in st.session_state:
        st.session_state.first_run = True
        data = await update_data()
    else:
        data = load_data_from_cache()
        current_time = datetime.now(pytz.utc)
        
        if data is None or (current_time - datetime.strptime(data['last_updated'], "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=pytz.UTC)) > timedelta(hours=4):
            data = await update_data()

    if data is not None:
        # Binance Section
        st.header("Binance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Binance Spot Data:")
            display_volume_data(data['binance_spot'], "Spot")
        
        with col2:
            st.write("Binance Futures Data:")
            display_volume_data(data['binance_futures'], "Perpetual")

        st.markdown("---")

        # Bybit Section
        st.header("Bybit")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Bybit Spot Data:")
            display_volume_data(data['bybit_spot'], "Spot")
        
        with col2:
            st.write("Bybit Perpetual Data:")
            display_volume_data(data['bybit_perp'], "Perpetual")


        # 最後の更新時間と次の更新時間を表示
        st.markdown(f"<p class='update-time'>Last updated: {data['last_updated']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='update-time'>Next update: {get_next_update_time()}</p>", unsafe_allow_html=True)
    else:
        st.error("データを取得できませんでした。後でもう一度お試しください。")

    if st.button("データを更新"):
        data = await update_data()
        st.experimental_rerun()

    # 定期更新タスク
    while True:
        now = datetime.now(pytz.utc)
        next_update = now.replace(hour=(now.hour // 4) * 4, minute=0, second=0, microsecond=0) + timedelta(hours=4)
        wait_time = (next_update - now).total_seconds()
        await asyncio.sleep(wait_time)
        await update_data()

async def start_discord_client():
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Discord clientの接続とStreamlitアプリの実行を並行して行う
    discord_task = loop.create_task(start_discord_client())
    app_task = loop.create_task(run_app())
    
    try:
        loop.run_until_complete(asyncio.gather(discord_task, app_task))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()