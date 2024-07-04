import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_fetcher import get_binance_data

class TestDataFetcher(unittest.TestCase):

    @patch('src.data_fetcher.Client')
    def test_get_binance_data_success(self, mock_client):
        # モックデータの準備
        mock_klines = [
            [1625097600000, "35000", "36000", "34000", "35500", "100", 1625183999999, "3550000", 1000, "50", "1775000", "0"],
            [1625184000000, "35500", "37000", "35000", "36500", "120", 1625270399999, "4380000", 1200, "60", "2190000", "0"]
        ]
        mock_client.return_value.get_historical_klines.return_value = mock_klines

        # テスト用のパラメータ
        symbol = 'BTCUSDT'
        interval = '1h'
        start_time = datetime(2021, 7, 1)
        end_time = datetime(2021, 7, 2)

        # 関数の実行
        result = get_binance_data(mock_client(), symbol, interval, start_time, end_time)

        # 結果の検証
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.index.name, 'timestamp')
        self.assertTrue('close' in result.columns)
        self.assertEqual(result['close'].dtype, float)

    @patch('src.data_fetcher.Client')
    def test_get_binance_data_empty_response(self, mock_client):
        # エッジケース: APIが空のレスポンスを返す場合
        mock_client.return_value.get_historical_klines.return_value = []
        
        symbol = 'BTCUSDT'
        interval = '1h'
        start_time = datetime.now()
        end_time = datetime.now() + timedelta(hours=1)
        
        result = get_binance_data(mock_client(), symbol, interval, start_time, end_time)
        
        self.assertTrue(result.empty)

    @patch('src.data_fetcher.Client')
    def test_get_binance_data_api_error(self, mock_client):
        # エラーケース: APIがエラーを返す場合
        mock_client.return_value.get_historical_klines.side_effect = Exception("API Error")
        
        symbol = 'BTCUSDT'
        interval = '1h'
        start_time = datetime.now()
        end_time = datetime.now() + timedelta(hours=1)
        
        with self.assertRaises(Exception):
            get_binance_data(mock_client(), symbol, interval, start_time, end_time)

if __name__ == '__main__':
    unittest.main()