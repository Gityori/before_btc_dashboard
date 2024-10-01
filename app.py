import streamlit as st
from io import StringIO
import sys
import os

# モジュールのインポート（上記の方法1または方法2を使用）
# 方法1を使用する場合
page_dir = os.path.join(os.path.dirname(__file__), 'page')
sys.path.append(page_dir)
import binance_test_api

# 方法2を使用する場合（`page`フォルダに`__init__.py`が必要）
# from page import binance_test_api

def binance_api_test_page():
    st.title("Binance APIテストページ")

    # 標準出力をキャプチャ
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    # test_binance_api()を実行
    binance_test_api.test_binance_api()

    # 標準出力を元に戻す
    sys.stdout = old_stdout

    # キャプチャした出力を取得
    output = mystdout.getvalue()

    # 出力を表示
    st.text_area("APIリクエスト結果", output, height=300)

# サイドバーでページを選択できるようにする
st.sidebar.title("メニュー")
page = st.sidebar.selectbox("ページを選択", ["ホーム", "Binance APIテスト"])

if page == "ホーム":
    # 既存のホームページの内容
    st.write("ホームページの内容をここに記述します。")
elif page == "Binance APIテスト":
    binance_api_test_page()
