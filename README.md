BINANCE BTCUSDT SPOT 分析
このプロジェクトは、Binanceにおける過去90日間のBTCUSDTスポット価格の変動率を分析します。曜日ごと、時間ごとの価格変化率を棒グラフで表示し、曜日と時間の組み合わせによる変化率をヒートマップで可視化します。
プロジェクト構造
btc-dashboard/
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py
│   ├── data_processor.py
│   └── visualizer.py
├── tests/
│   ├── __init__.py
│   ├── test_data_fetcher.py
│   ├── test_data_processor.py
│   └── test_visualizer.py
├── app.py
├── requirements.txt
└── README.md

src/: プロジェクトの主要機能を含むディレクトリ

data_fetcher.py: Binance APIからデータを取得
data_processor.py: 取得したデータを処理
visualizer.py: 処理されたデータの可視化を作成


tests/: 主要機能のユニットテストを含むディレクトリ
app.py: Streamlitダッシュボードを実行するメインアプリケーションファイル
requirements.txt: 必要なPythonパッケージのリスト

セットアップ

仮想環境を作成します（推奨）：
python -m venv venv
source venv/bin/activate  # Windowsの場合は `venv\Scripts\activate`

必要なパッケージをインストールします：
pip install -r requirements.txt

ルートディレクトリに .env ファイルを作成し、Binance APIの認証情報を追加します：
BINANCE_API_KEY=あなたのBinance APIキー
BINANCE_API_SECRET=あなたのBinance APIシークレット


使用方法
Streamlitダッシュボードを実行するには：
streamlit run app.py
これにより、アプリケーションが起動し、デフォルトのWebブラウザで開きます。ダッシュボードには以下が表示されます：

曜日ごとの価格変化率を示す棒グラフ
時間ごとの価格変化率を示す棒グラフ
曜日と時間の組み合わせによる価格変化率を示すヒートマップ

データは1時間ごとに自動更新されます。ページ下部のスイッチで自動更新のオン/オフを切り替えることができます。
テストの実行
全てのテストを実行するには：
python -m unittest discover tests
個別のテストファイルを実行するには：
python tests/test_data_fetcher.py
python tests/test_data_processor.py
python tests/test_visualizer.py