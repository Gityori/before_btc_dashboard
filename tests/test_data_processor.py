import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from calculate_heatmap import process_data, calculate_depth_ratio, process_depth_data, detect_anomalies

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        # テストデータの準備
        dates = pd.date_range(start='2021-01-01', end='2021-01-07', freq='H')
        self.test_data = pd.DataFrame({
            'close': np.random.randn(len(dates)) * 100 + 35000
        }, index=dates)

    def test_process_data(self):
        weekday_return, hour_return, heatmap_data = process_data(self.test_data)

        # 結果の検証
        self.assertIsInstance(weekday_return, pd.Series)
        self.assertEqual(len(weekday_return), 7)  # 7日分のデータ

        self.assertIsInstance(hour_return, pd.Series)
        self.assertEqual(len(hour_return), 24)  # 24時間分のデータ

        self.assertIsInstance(heatmap_data, pd.DataFrame)
        self.assertEqual(heatmap_data.shape, (7, 24))  # 7日 x 24時間のヒートマップ

    def test_process_data_empty_input(self):
        empty_data = pd.DataFrame()
        weekday_return, hour_return, heatmap_data = process_data(empty_data)

        self.assertTrue(weekday_return.empty)
        self.assertTrue(hour_return.empty)
        self.assertTrue(heatmap_data.empty)

    def test_calculate_depth_ratio(self):
        depth_data = {
            'spot_bid_depth': 100,
            'spot_ask_depth': 120,
            'perp_bid_depth': 150,
            'perp_ask_depth': 170
        }
        ratio = calculate_depth_ratio(depth_data)
        self.assertAlmostEqual(ratio, 0.6875, places=4)

    def test_process_depth_data(self):
        depth_data_list = [
            {
                'timestamp': datetime(2021, 1, 1, 12, 0),
                'spot_bid_depth': 100,
                'spot_ask_depth': 120,
                'perp_bid_depth': 150,
                'perp_ask_depth': 170
            },
            {
                'timestamp': datetime(2021, 1, 1, 12, 5),
                'spot_bid_depth': 110,
                'spot_ask_depth': 130,
                'perp_bid_depth': 160,
                'perp_ask_depth': 180
            }
        ]
        result = process_depth_data(depth_data_list)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertTrue('depth_ratio' in result.columns)

    def test_detect_anomalies(self):
        dates = pd.date_range(start='2021-01-01', end='2021-01-02', freq='5T')
        depth_ratios = pd.Series(np.random.randn(len(dates)) * 0.1 + 1, index=dates)
        # Add an anomaly
        depth_ratios.iloc[100] = 5

        anomalies = detect_anomalies(depth_ratios)
        self.assertIsInstance(anomalies, pd.Series)
        self.assertTrue(anomalies.iloc[100])
        self.assertTrue(anomalies.sum() > 0)  # At least one anomaly detected

if __name__ == '__main__':
    unittest.main()