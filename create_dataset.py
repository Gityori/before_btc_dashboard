from google.cloud import bigquery
from google.oauth2 import service_account

def init_client() -> bigquery.Client:
    key_path = "C:/Users/kikuchi/Dropbox/Python Scripts/crypto_monitor/btc-dashboard/test-depth-visualize-b3460b9bf594.json"
    credentials = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

def create_dataset(client: bigquery.Client):
    dataset_id = "{}.sample_dataset".format(client.project)
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "asia-northeast1"
    client.create_dataset(dataset)

if __name__ == "__main__":
    client = init_client()
    create_dataset(client)