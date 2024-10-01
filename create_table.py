from google.cloud import bigquery
from google.oauth2 import service_account

def init_client() -> bigquery.Client:
    key_path = "C:/Users/kikuchi/Dropbox/Python Scripts/crypto_monitor/btc-dashboard/test-depth-visualize-b3460b9bf594.json"
    credentials = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

def create_table(client: bigquery.Client):
    dataset_id = "{}.sample_dataset".format(client.project)
    dataset = client.get_dataset(dataset_id)

    table_id = "{}.{}.sample_table_name".format(client.project, dataset.dataset_id)
    schema = [
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("age", "INTEGER", mode="NULLABLE"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table)

if __name__ == "__main__":
    # init_client() は前述のものを使用
    client = init_client()
    create_table(client)