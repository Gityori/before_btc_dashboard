import pandas as pd
import numpy as np
from datetime import timedelta
import tarfile
import io
import logging

def process_5min_intervals(interval_data, start_time, end_time, close_price):
    # 価格範囲の計算
    lower_ask_price = close_price * 1.01
    upper_ask_price = close_price * 1.025
    lower_bid_price = close_price * 0.975
    upper_bid_price = close_price * 0.99
    ask_price_upper_1pct = close_price * 1.01
    bid_price_lower_1pct = close_price * 0.99
    ask_price_upper_5pct = close_price * 1.05
    bid_price_lower_5pct = close_price * 0.95

    # フィルタリングと集計
    filtered_data = interval_data[
        ((interval_data['side'] == 'a') & (interval_data['price'] >= lower_ask_price) & (interval_data['price'] <= upper_ask_price)) |
        ((interval_data['side'] == 'b') & (interval_data['price'] >= lower_bid_price) & (interval_data['price'] <= upper_bid_price))
    ]
    a_qty_sum = filtered_data[filtered_data['side'] == 'a']['qty'].sum()
    b_qty_sum = filtered_data[filtered_data['side'] == 'b']['qty'].sum()
    depth_ratio = a_qty_sum / b_qty_sum if b_qty_sum != 0 else np.inf

    data_within_1pct = interval_data[
        (interval_data['price'] >= bid_price_lower_1pct) & (interval_data['price'] <= ask_price_upper_1pct)
    ]
    total_qty_1pct = data_within_1pct['qty'].sum()

    data_within_5pct = interval_data[
        (interval_data['price'] >= bid_price_lower_5pct) & (interval_data['price'] <= ask_price_upper_5pct)
    ]
    total_qty_5pct = data_within_5pct['qty'].sum()

    result = pd.DataFrame([{
        'interval_start': start_time,
        'interval_end': end_time,
        'close_price': close_price,
        'a_qty_sum': a_qty_sum,
        'b_qty_sum': b_qty_sum,
        'depth_ratio': depth_ratio,
        'total_qty_1pct': total_qty_1pct,
        'total_qty_5pct': total_qty_5pct,
        'filtered_count': len(filtered_data)
    }])

    return result

def process_large_file(file_path, start_time, end_time, get_close_prices_func):
    total_rows = 0
    all_data = pd.DataFrame()

    with tarfile.open(file_path, 'r:gz') as tar:
        for member in tar.getmembers():
            f = tar.extractfile(member)
            if f is not None:
                # 必要なカラムのみを読み込む
                df = pd.read_csv(
                    io.TextIOWrapper(f),
                    dtype={
                        'timestamp': 'int64',
                        'price': 'float32',
                        'qty': 'float32',
                        'side': 'category'
                    },
                    usecols=['timestamp', 'price', 'qty', 'side']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                total_rows += len(df)
                all_data = pd.concat([all_data, df], ignore_index=True)
                break  # 最初のファイルのみを処理

    # 指定された期間のデータのみを残す
    all_data = all_data[(all_data['timestamp'] >= start_time) & (all_data['timestamp'] < end_time)]
    if all_data.empty:
        print("No data in the specified time range.")
        return pd.DataFrame()

    # 5分間隔の開始時刻リストを生成
    interval_starts = pd.date_range(start=start_time, end=end_time, freq='5T')

    # 必要な終値を取得
    close_prices = get_close_prices_func(interval_starts)

    # 各5分間隔での処理
    results = []
    for start in interval_starts:
        end = start + timedelta(minutes=5)
        interval_data = all_data[(all_data['timestamp'] >= start) & (all_data['timestamp'] < end)]
        if interval_data.empty:
            continue
        close_price = close_prices.get(start)
        if close_price is None:
            continue
        processed_interval = process_5min_intervals(interval_data, start, end, close_price)
        if not processed_interval.empty:
            results.append(processed_interval)

    if results:
        final_result = pd.concat(results, ignore_index=True)
        final_result['relative_ratio_percent'] = (final_result['depth_ratio'] - 1) * 100
        logging.info(f"Final result shape: {final_result.shape}")
        logging.info(f"Total rows processed: {total_rows}")
        return final_result
    else:
        print("No data processed.")
        return pd.DataFrame()
