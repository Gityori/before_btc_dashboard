import discord
import asyncio
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import pytz
import sys

# 親ディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.binance_top10 import get_binance_volume_top10
from src.bybit_top10 import get_bybit_volume_top10
from io import StringIO

# .envファイルを読み込む
load_dotenv()

class DiscordNotifier:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        self.cache_file = "volume_data_cache.json"

    def capture_output(self, func, *args, **kwargs):
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result
        func(*args, **kwargs)
        sys.stdout = old_stdout
        return result.getvalue()

    async def send_message(self, message):
        channel = self.client.get_channel(self.channel_id)
        if channel:
            await channel.send(message)
        else:
            print(f"Error: Channel with ID {self.channel_id} not found.")

    async def update_data(self):
        try:
            print("Fetching Binance spot data...")
            binance_spot = self.capture_output(get_binance_volume_top10, 'spot')
            print("Fetching Binance futures data...")
            binance_futures = self.capture_output(get_binance_volume_top10, 'futures')
            print("Fetching Bybit spot data...")
            bybit_spot = self.capture_output(get_bybit_volume_top10, 'spot')
            print("Fetching Bybit linear data...")
            bybit_futures = self.capture_output(get_bybit_volume_top10, 'linear')

            data = {
                'binance_spot': binance_spot,
                'binance_futures': binance_futures,
                'bybit_spot': bybit_spot,
                'bybit_futures': bybit_futures,
                'last_updated': datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            
            self.save_data_to_cache(data)

            message = "取引量トップ10更新\n\n"
            message += f"Binance スポット取引:\n```\n{binance_spot}```\n"
            message += f"Binance 先物取引:\n```\n{binance_futures}```\n"
            message += f"Bybit スポット取引:\n```\n{bybit_spot}```\n"
            message += f"Bybit 永続先物取引:\n```\n{bybit_futures}```\n"

            await self.send_message(message)
            print("Discord message sent successfully!")

            return data
        except Exception as e:
            error_message = f"データ取得中にエラーが発生しました: {str(e)}"
            print(f"Error: {error_message}")
            await self.send_message(error_message)
            return None

    def save_data_to_cache(self, data):
        with open(self.cache_file, 'w') as f:
            json.dump(data, f)

    def load_data_from_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return None

    async def check_and_send_updates(self):
        while True:
            data = self.load_data_from_cache()
            if data:
                current_time = datetime.now(pytz.utc)
                last_updated = datetime.strptime(data['last_updated'], "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=pytz.UTC)
                
                if (current_time - last_updated) > timedelta(minutes=1):
                    await self.update_data()
            
            await asyncio.sleep(60)  # 1分待機

    async def start(self):
        @self.client.event
        async def on_ready():
            print(f'{self.client.user} has connected to Discord!')
            self.client.loop.create_task(self.check_and_send_updates())

        await self.client.start(self.token)

if __name__ == "__main__":
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
    
    notifier = DiscordNotifier(DISCORD_TOKEN, CHANNEL_ID)
    asyncio.run(notifier.start())