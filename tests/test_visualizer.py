import unittest
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.visualizer import create_weekday_plot, create_hourly_plot, create_heatmap, create_depth_ratio_plot

class TestVisualizer(unittest.TestCase):

    def setUp(self):
        # テストデータの準備
        self.weekday_return = pd.Series(np.random.randn(7) * 0.01, index=range(7))
        self.hour_return = pd.Series(np.random.randn(24) * 0.01, index=range(24))
        self.heatmap_data = pd.DataFrame(np.random.randn(7, 24) * 0.01)
        # 新しいテストデータ: 板の厚み比率
        dates = pd.date_range(start='2021-01-01', end='2021-01-02', freq='5T')
        self.depth_ratio_data = pd.DataFrame({
            'depth_ratio': np.random.randn(len(dates)) * 0.5 + 1  # 平均1、標準偏差0.5の正規分布
        }, index=dates)

    def test_create_weekday_plot(self):
        fig = create_weekday_plot(self.weekday_return)
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)  # 1つのトレース（棒グラフ）があることを確認
        self.assertEqual(fig.data[0].type, 'bar')
        self.assertEqual(len(fig.data[0].x), 7)  # 7日分のデータ
        self.assertEqual(len(fig.data[0].y), 7)  # 7日分のデータ

    def test_create_hourly_plot(self):
        fig = create_hourly_plot(self.hour_return)
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)  # 1つのトレース（棒グラフ）があることを確認
        self.assertEqual(fig.data[0].type, 'bar')
        self.assertEqual(len(fig.data[0].x), 24)  # 24時間分のデータ
        self.assertEqual(len(fig.data[0].y), 24)  # 24時間分のデータ

    def test_create_heatmap(self):
        fig = create_heatmap(self.heatmap_data)
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)  # 1つのトレース（ヒートマップ）があることを確認
        self.assertEqual(fig.data[0].type, 'heatmap')
        self.assertEqual(fig.data[0].z.shape, (7, 24))  # 7日 x 24時間のヒートマップ

     # 新しいテスト関数: 板の厚み比率のグラフ作成
    def test_create_depth_ratio_plot(self):
        fig = create_depth_ratio_plot(self.depth_ratio_data)
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 2)  # 2つのトレース（スポットと先物）があることを確認
        self.assertEqual(fig.data[0].type, 'bar')
        self.assertEqual(fig.data[1].type, 'bar')
        self.assertEqual(len(fig.data[0].x), len(self.depth_ratio_data))
        self.assertEqual(len(fig.data[1].x), len(self.depth_ratio_data))

    def test_visualizer_functions_with_empty_data(self):
        # エッジケース: 空のデータでの動作確認
        empty_series = pd.Series()
        empty_df = pd.DataFrame()

        weekday_fig = create_weekday_plot(empty_series)
        self.assertIsNotNone(weekday_fig)
        self.assertEqual(len(weekday_fig.data[0].x), 0)
        self.assertEqual(len(weekday_fig.data[0].y), 0)

        hourly_fig = create_hourly_plot(empty_series)
        self.assertIsNotNone(hourly_fig)
        self.assertEqual(len(hourly_fig.data[0].x), 0)
        self.assertEqual(len(hourly_fig.data[0].y), 0)

        heatmap_fig = create_heatmap(empty_df)
        self.assertIsNotNone(heatmap_fig)
        self.assertEqual(heatmap_fig.data[0].z.shape, (0, 0))

if __name__ == '__main__':
    unittest.main()