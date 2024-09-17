import plotly.graph_objs as go
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_y_range(values):
    if len(values) == 0:  # 配列が空かどうかを確認
        return 0, 1  # 空の場合はデフォルトの範囲を設定
    y_min = min(values)
    y_max = max(values)
    y_range = y_max - y_min
    y_padding = y_range * 0.1  # パディングを追加してグラフの見栄えを良くする
    return y_min - y_padding, y_max + y_padding


def create_weekday_plot(weekday_return: pd.Series) -> go.Figure:
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    # データが空かどうかをチェック
    if weekday_return.empty:
        x_data = []
        y_data = []
    else:
        x_data = weekdays
        y_data = weekday_return.values

    fig = go.Figure(data=[
        go.Bar(x=x_data, y=y_data, width=0.5)
    ])

    if not weekday_return.empty:
        y_min, y_max = get_y_range(weekday_return.values)
        fig.update_layout(
            yaxis=dict(
                range=[y_min, y_max],
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='lightgrey'
            )
        )

    fig.update_layout(
        title='曜日ごとの価格変化率',
        xaxis_title='曜日',
        yaxis_title='平均変化率 (%)',
        margin=dict(l=50, r=50, t=50, b=50),
        height=400,
        width=500
    )

    return fig

def create_hourly_plot(hour_return: pd.Series) -> go.Figure:
    hours = list(range(24))
    if hour_return.empty:
        x_data = []
        y_data = []
    else:
        x_data = hours
        y_data = hour_return.values

    fig = go.Figure(data=[
        go.Bar(x=x_data, y=y_data, width=0.5)
    ])

    if not hour_return.empty:
        y_min, y_max = get_y_range(hour_return.values)
        fig.update_layout(
            yaxis=dict(
                range=[y_min, y_max],
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='lightgrey'
            )
        )

    fig.update_layout(
        title='時間ごとの価格変化率',
        xaxis_title='時間',
        yaxis_title='平均変化率 (%)',
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1
        ),
        height=400,
        width=500
    )

    return fig

def create_heatmap(heatmap_data: pd.DataFrame) -> go.Figure:
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    hours = list(range(24))

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=hours,
        y=weekdays,
        colorscale='RdBu_r'
    ))

    fig.update_layout(
        title='曜日・時間ごとの価格変化率ヒートマップ'
    )

    fig.update_xaxes(
        tickmode='array',
        tickvals=hours,
        ticktext=[f"{h}" for h in hours]
    )

    fig.update_yaxes(
        tickmode='array',
        tickvals=weekdays,
        ticktext=weekdays
    )

    num_cells = len(weekdays)
    cell_size = 75
    fig_height = num_cells * cell_size
    fig_width = len(hours) * cell_size

    fig.update_layout(
        autosize=False,
        width=fig_width,
        height=fig_height
    )

    return fig

# 新しい関数: 板の厚み比率のグラフを作成
def create_depth_ratio_plot(depth_ratio_data: pd.DataFrame) -> go.Figure:
    """
    Create a plot of the order book depth ratio between spot and perpetual markets.
    
    :param depth_ratio_data: DataFrame with 'timestamp' index and 'depth_ratio' column
    :return: Plotly Figure object
    """
    fig = go.Figure()

    # スポット市場の深さ（正の値）
    fig.add_trace(go.Bar(
        x=depth_ratio_data.index,
        y=depth_ratio_data['depth_ratio'].clip(lower=0),
        name='Spot Depth',
        marker_color='green'
    ))

    # 先物市場の深さ（負の値）
    fig.add_trace(go.Bar(
        x=depth_ratio_data.index,
        y=-depth_ratio_data['depth_ratio'].clip(upper=0),
        name='Perp Depth',
        marker_color='orange'
    ))

    # レイアウトの設定
    fig.update_layout(
        title='Order Book Depth Ratio: Spot vs Perpetual',
        xaxis_title='Time',
        yaxis_title='Depth Ratio (Spot / Perp)',
        barmode='relative',
        yaxis=dict(
            tickformat='.2f',
            range=[-max(abs(depth_ratio_data['depth_ratio'].min()), depth_ratio_data['depth_ratio'].max()) * 1.1,
                   max(abs(depth_ratio_data['depth_ratio'].min()), depth_ratio_data['depth_ratio'].max()) * 1.1]
        )
    )

    return fig

def create_depth_ratio_plot(depth_ratio_data: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart of the order book depth ratio over time, with positive and negative values.
    
    :param depth_ratio_data: DataFrame with 'timestamp' index and 'depth_ratio' column
    :return: Plotly Figure object
    """
    fig = go.Figure()

    # 正の値（緑）
    fig.add_trace(go.Bar(
        x=depth_ratio_data.index,
        y=depth_ratio_data['depth_ratio'].clip(lower=0),
        name='Positive Depth Ratio',
        marker_color='green'
    ))

    # 負の値（オレンジ）
    fig.add_trace(go.Bar(
        x=depth_ratio_data.index,
        y=depth_ratio_data['depth_ratio'].clip(upper=0),
        name='Negative Depth Ratio',
        marker_color='orange'
    ))

    fig.update_layout(
        title='Order Book Depth Ratio (1-2.5%)',
        xaxis_title='Time',
        yaxis_title='Depth Ratio',
        barmode='relative',
        yaxis=dict(
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='white',
            tickformat='.2f'
        ),
        plot_bgcolor='rgb(30,30,30)',
        paper_bgcolor='rgb(30,30,30)',
        font=dict(color='white'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    # Y軸の範囲を設定
    max_abs_value = max(abs(depth_ratio_data['depth_ratio'].max()), abs(depth_ratio_data['depth_ratio'].min()))
    fig.update_yaxes(range=[-max_abs_value * 1.1, max_abs_value * 1.1])

    # X軸のグリッドラインを追加
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(255,255,255,0.1)'
    )

    fig.update_xaxes(rangeslider_visible=True)

    return fig


def create_combined_chart(depth_ratio_df, price_df):
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.4, 0.2, 0.2, 0.2]
    )
    # BTCUSDTの価格チャート
    fig.add_trace(
        go.Scatter(
            x=price_df['timestamp'], 
            y=price_df['close'], 
            name='BTCUSDT Price'
        ), 
        row=1, col=1
    )
    # Depth Ratioのバーチャート
    fig.add_trace(
        go.Bar(
            x=depth_ratio_df['interval_start'], 
            y=depth_ratio_df['relative_ratio_percent'], 
            name='Depth Ratio (%)'
        ), 
        row=2, col=1
    )
    # 1%以内の総合計量
    fig.add_trace(
        go.Bar(
            x=depth_ratio_df['interval_start'], 
            y=depth_ratio_df['total_qty_1pct'], 
            name='Total Volume within 1%', 
            marker_color='blue'
        ), 
        row=3, col=1
    )
    # 5%以内の総合計量
    fig.add_trace(
        go.Bar(
            x=depth_ratio_df['interval_start'], 
            y=depth_ratio_df['total_qty_5pct'], 
            name='Total Volume within 5%', 
            marker_color='orange'
        ), 
        row=4, col=1
    )
    # レイアウトの更新
    fig.update_layout(
        height=1000, 
        title_text="BTCUSDT Price and Depth Metrics"
    )
    fig.update_xaxes(title_text="Time", row=4, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Depth Ratio (%)", row=2, col=1)
    fig.update_yaxes(title_text="Total Volume within 1%", row=3, col=1)
    fig.update_yaxes(title_text="Total Volume within 5%", row=4, col=1)
    # 凡例の位置調整
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    return fig
