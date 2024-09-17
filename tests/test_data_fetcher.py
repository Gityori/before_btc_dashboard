import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_fetcher import get_binance_data, calculate_depth, get_depth_data, fetch_depth_data

class TestDataFetcher(unittest.TestCase):

    def test_get_binance_data(self):
        mock_client = MagicMock()
        mock_client.get_historical_klines.return_value = [
            [1625097600000, "35000", "36000", "34000", "35500", "100", 1625183999999, "3550000", 1000, "50", "1775000", "0"],
            [1625184000000, "35500", "37000", "35000", "36500", "120", 1625270399999, "4380000", 1200, "60", "2190000", "0"]
        ]

        start_time = datetime(2021, 7, 1)
        end_time = datetime(2021, 7, 2)
        result = get_binance_data(mock_client, 'BTCUSDT', '1h', start_time, end_time)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.index.name, 'timestamp')
        self.assertTrue('close' in result.columns)
        self.assertEqual(result['close'].dtype, float)

    def test_calculate_depth(self):
        bids = [['34000', '1.0'], ['33900', '2.0'], ['33800', '3.0']]
        asks = [['34100', '1.5'], ['34200', '2.5'], ['34300', '3.5']]
        bid_depth, ask_depth = calculate_depth(bids, asks, 0.025)
        self.assertGreater(bid_depth, 0)
        self.assertGreater(ask_depth, 0)

    @patch('src.data_fetcher.get_binance_orderbook_data')
    def test_get_depth_data(self, mock_get_orderbook):
        mock_spot_depth = {'bids': [['34000', '1.0']], 'asks': [['34100', '1.5']]}
        mock_perp_depth = {'bids': [['34050', '1.2']], 'asks': [['34150', '1.7']]}
        mock_get_orderbook.return_value = (mock_spot_depth, mock_perp_depth)

        mock_client = MagicMock()
        result = get_depth_data(mock_client, 'BTCUSDT')

        self.assertIsNotNone(result)
        self.assertIn('timestamp', result)
        self.assertIn('spot_bid_depth', result)
        self.assertIn('spot_ask_depth', result)
        self.assertIn('perp_bid_depth', result)
        self.assertIn('perp_ask_depth', result)

    @patch('src.data_fetcher.get_depth_data')
    def test_fetch_depth_data(self, mock_get_depth_data):
        mock_depth_data = {
            'timestamp': datetime.now(),
            'spot_bid_depth': 100,
            'spot_ask_depth': 110,
            'perp_bid_depth': 120,
            'perp_ask_depth': 130
        }
        mock_get_depth_data.return_value = mock_depth_data

        mock_client = MagicMock()
        generator = fetch_depth_data(mock_client, 'BTCUSDT', interval=1)
        result = next(generator)

        self.assertEqual(result, mock_depth_data)

if __name__ == '__main__':
    unittest.main()