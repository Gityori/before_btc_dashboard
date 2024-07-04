import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_processor import process_data

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

if __name__ == '__main__':
    unittest.main()