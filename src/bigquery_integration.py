import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

def upload_dataframe_to_bigquery(dataframe, dataset_id, table_id, service_account_key_path, location="US"):
    """
    DataFrameを直接BigQueryにアップロードする関数。
    必要な4つのフィールド以外のフィールドを削除してアップロードします。
    """
    client = bigquery.Client.from_service_account_json(service_account_key_path)

    # 必要な4つのフィールドだけを選択
    required_columns = ['interval_end', 'depth_ratio', 'total_qty_1pct', 'total_qty_5pct']
    dataframe = dataframe[required_columns]  # 必要なフィールドのみを保持

    # スキーマ定義（interval_endをTIMESTAMPとして使用）
    schema = [
        bigquery.SchemaField("interval_end", "TIMESTAMP"),  # タイムスタンプ型
        bigquery.SchemaField("depth_ratio", "FLOAT"),       # 浮動小数点型
        bigquery.SchemaField("total_qty_1pct", "FLOAT"),    # 浮動小数点型
        bigquery.SchemaField("total_qty_5pct", "FLOAT"),    # 浮動小数点型
    ]

    # データセットの存在を確認し、なければ作成する
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)  # データセットが存在するかチェック
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location  # データセットの場所を指定
        client.create_dataset(dataset)
        print(f"データセット {dataset_id} を作成しました。")

    # テーブルの存在を確認し、なければ作成する
    table_ref = dataset_ref.table(table_id)
    try:
        client.get_table(table_ref)  # テーブルが存在するかチェック
    except NotFound:
        table = bigquery.Table(table_ref, schema=schema)
        client.create_table(table)
        print(f"テーブル {table_id} を作成しました。")

    # ジョブ設定
    job_config = bigquery.LoadJobConfig()
    job_config.autodetect = False  # スキーマは手動設定なので自動検出を無効化
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND  # データを追加

    # データのアップロード
    job = client.load_table_from_dataframe(dataframe, table_ref, job_config=job_config)
    job.result()  # 完了を待機

    print(f"データをテーブル {table_id} にアップロードしました。")
