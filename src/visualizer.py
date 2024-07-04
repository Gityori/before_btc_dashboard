import plotly.graph_objs as go
import pandas as pd

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