import pandas as pd
import numpy as np

def process_data(data: pd.DataFrame) -> tuple:
    """
    Process the raw price data to calculate return rates.
    
    :param data: Raw DataFrame containing price data
    :return: Tuple containing weekday_return, hour_return, and heatmap_data
    """
    # 空のDataFrameまたは必要なカラムが欠けている場合、適切なデフォルト値を返します。
    if data.empty or 'close' not in data.columns:
        empty_series = pd.Series(dtype=float)
        empty_df = pd.DataFrame()
        return empty_series, empty_series, empty_df
    
    # 収益率の計算
    data['return'] = data['close'].pct_change()
    data['weekday'] = data.index.weekday
    data['hour'] = data.index.hour
    
    # 各曜日と時間ごとの収益率の平均を計算し、パーセンテージに変換
    weekday_return = data.groupby('weekday')['return'].mean() * 100  # Convert to percentage
    hour_return = data.groupby('hour')['return'].mean() * 100  # Convert to percentage
    
    # ヒートマップデータの作成
    heatmap_data = data.pivot_table(index='weekday', columns='hour', values='return', aggfunc='mean') * 100  # Convert to percentage
    
    return weekday_return, hour_return, heatmap_data