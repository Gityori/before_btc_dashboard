import streamlit as st
import requests
import sys
from io import StringIO

def test_binance_api():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス内容の一部: {response.text[:500]}")  # レスポンスの最初の500文字を表示
    except Exception as e:
        print(f"エラー: {e}")

def main():
    st.title("Binance APIテストページ")

    # 標準出力をキャプチャ
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    # test_binance_api()を実行
    test_binance_api()

    # 標準出力を元に戻す
    sys.stdout = old_stdout

    # キャプチャした出力を取得
    output = mystdout.getvalue()

    # 出力を表示
    st.text_area("APIリクエスト結果", output, height=300)

if __name__ == "__main__":
    main()
