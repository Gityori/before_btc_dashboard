import os
import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
import pytz
from typing import Optional, Dict, Any, Tuple
import pandas as pd

class DiscordNotifier:
    _instance = None

    def __new__(cls, webhook_url: str, cache_file: str = "volume_data_cache.json"):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, webhook_url: str, cache_file: str = "volume_data_cache.json"):
        """
        Discord通知クラスの初期化
        
        Args:
            webhook_url (str): DiscordのWebhook URL
            cache_file (str): キャッシュファイルのパス
        """
        if not hasattr(self, 'initialized'):
            self.webhook_url = webhook_url
            self.cache_file = cache_file
            self.session: Optional[aiohttp.ClientSession] = None
            
            # ロギングの設定
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger('DiscordNotifier')
            self.initialized = True

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリーポイント"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了処理"""
        if self.session:
            await self.session.close()
            self.session = None

    def format_volume_data(self, data: Dict[str, Any]) -> str:
        """
        取引量データをDiscordメッセージ形式に整形
        
        Args:
            data: 取引量データの辞書
        Returns:
            str: フォーマットされたメッセージ
        """
        message_parts = []
        
        if 'binance_spot' in data:
            message_parts.append("**Binance Spot Top 10**\n```\n" + data['binance_spot'] + "\n```")
        if 'binance_futures' in data:
            message_parts.append("**Binance Futures Top 10**\n```\n" + data['binance_futures'] + "\n```")
        if 'bybit_spot' in data:
            message_parts.append("**Bybit Spot Top 10**\n```\n" + data['bybit_spot'] + "\n```")
        if 'bybit_perp' in data:
            message_parts.append("**Bybit Perpetual Top 10**\n```\n" + data['bybit_perp'] + "\n```")

        return "\n\n".join(message_parts)

    async def send_message(self, content: str, is_page_load: bool = False) -> bool:
        """
        Discordにメッセージを送信
        
        Args:
            content: 送信するメッセージ内容
            is_page_load: ページロード時の通知かどうか
        Returns:
            bool: 送信成功したかどうか
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        # ページロード時の場合、プレフィックスを追加
        if is_page_load:
            content = "**🔄 Page Reload Update**\n" + content

        # メッセージを2000文字以内に制限
        if len(content) > 2000:
            contents = [content[i:i+1900] for i in range(0, len(content), 1900)]
        else:
            contents = [content]

        try:
            for content_part in contents:
                payload = {'content': content_part}
                async with self.session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        self.logger.info("Message sent successfully")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to send message. Status: {response.status}, Response: {error_text}")
                        return False
                    
                    # Discord rate limitを考慮して待機
                    await asyncio.sleep(1)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return False
        finally:
            if is_page_load and self.session:
                await self.session.close()
                self.session = None

    def save_to_cache(self, data: Dict[str, Any]) -> None:
        """キャッシュにデータを保存"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            self.logger.error(f"Error saving cache: {str(e)}")

    def load_from_cache(self) -> Optional[Dict[str, Any]]:
        """キャッシュからデータを読み込み"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading cache: {str(e)}")
        return None

    async def update_and_notify(self, volume_data: Dict[str, Any], is_page_load: bool = False) -> bool:
        """
        データを更新してDiscordに通知
        
        Args:
            volume_data: 更新する取引量データ
            is_page_load: ページロード時の通知かどうか
        Returns:
            bool: 更新と通知が成功したかどうか
        """
        try:
            # タイムスタンプを追加
            volume_data['last_updated'] = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # キャッシュに保存
            self.save_to_cache(volume_data)
            
            # メッセージをフォーマット
            message = "**Trading Volume Update**\n" + self.format_volume_data(volume_data)
            
            # Discordに送信
            return await self.send_message(message, is_page_load)
            
        except Exception as e:
            self.logger.error(f"Error in update_and_notify: {str(e)}")
            return False

    def should_update(self) -> Tuple[bool, datetime]:
        """
        更新が必要かどうかを判断
        
        Returns:
            Tuple[bool, datetime]: (更新が必要かどうか, 次の更新時刻)
        """
        now = datetime.now(pytz.UTC)
        next_hour = (now.hour // 4 + 1) * 4
        next_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
        
        if next_hour >= 24:
            next_time = next_time + timedelta(days=1)
            next_time = next_time.replace(hour=0)

        cached_data = self.load_from_cache()
        if not cached_data:
            return True, next_time

        last_updated = datetime.strptime(
            cached_data['last_updated'],
            "%Y-%m-%d %H:%M:%S UTC"
        ).replace(tzinfo=pytz.UTC)

        # 4時間ごとの更新時刻かどうかをチェック
        is_update_hour = now.hour % 4 == 0 and now.minute < 5
        is_old_data = now - last_updated > timedelta(hours=4)

        return (is_update_hour or is_old_data), next_time

async def run_notifier(webhook_url: str):
    """
    通知処理のメインループ
    
    Args:
        webhook_url: DiscordのWebhook URL
    """
    async with DiscordNotifier(webhook_url) as notifier:
        while True:
            try:
                should_update, next_time = notifier.should_update()
                
                if should_update:
                    # ここで新しいデータを取得（実際の実装に合わせて修正）
                    # fetch_latest_data()の実装は別途必要
                    new_data = notifier.load_from_cache()  # この行は実際のデータ取得処理に置き換える
                    if new_data:
                        await notifier.update_and_notify(new_data)
                
                # 次の更新までの待機時間を計算
                now = datetime.now(pytz.UTC)
                sleep_seconds = (next_time - now).total_seconds()
                await asyncio.sleep(max(60, sleep_seconds))  # 最小1分の待機時間
                
            except Exception as e:
                notifier.logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(300)  # エラー時は5分待機

# Streamlitページ用の関数
async def notify_on_page_load(webhook_url: str) -> None:
    """
    ページロード時に通知を送信
    
    Args:
        webhook_url: DiscordのWebhook URL
    """
    notifier = DiscordNotifier(webhook_url)
    cached_data = notifier.load_from_cache()
    if cached_data:
        await notifier.update_and_notify(cached_data, is_page_load=True)

# Streamlitページでの使用例
def initialize_notifications():
    """Streamlitページの初期化時に呼び出す関数"""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url:
        asyncio.run(notify_on_page_load(webhook_url))

if __name__ == "__main__":
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL environment variable is not set")
    
    # メインループを実行
    asyncio.run(run_notifier(webhook_url))