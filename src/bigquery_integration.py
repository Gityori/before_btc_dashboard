from google.cloud import bigquery
import pandas as pd

class BigQueryStorage:
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        self.client = bigquery.Client(project=project_id)
        self.table_id = f"{project_id}.{dataset_id}.{table_id}"

    def save_data(self, data: pd.DataFrame):
        job_config = bigquery.LoadJobConfig(
            autodetect=True,
            write_disposition="WRITE_APPEND",
        )

        job = self.client.load_table_from_dataframe(
            data, self.table_id, job_config=job_config
        )

        job.result()  # Wait for the job to complete

        print(f"Loaded {job.output_rows} rows into {self.table_id}")