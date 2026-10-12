"""Chargement BigQuery (load jobs uniquement : compatible avec le bac à sable gratuit)."""

import io

from google.cloud import bigquery

from ingestion import config
from ingestion.transform import vers_ndjson


def client() -> bigquery.Client:
    return bigquery.Client(project=config.exiger_projet(), location=config.BQ_LOCATION)


def creer_dataset_si_absent(bq: bigquery.Client, dataset_id: str) -> None:
    dataset = bigquery.Dataset(f"{bq.project}.{dataset_id}")
    dataset.location = config.BQ_LOCATION
    bq.create_dataset(dataset, exists_ok=True)


def charger(
    bq: bigquery.Client,
    lignes: list[dict],
    destination: str,
    schema: list[bigquery.SchemaField],
    partition_field: str | None = None,
) -> int:
    """Remplace la table (ou la partition visée par un décorateur $AAAAMMJJ)."""
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    if partition_field:
        job_config.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY, field=partition_field
        )
    job = bq.load_table_from_file(
        io.BytesIO(vers_ndjson(lignes)), destination, job_config=job_config
    )
    job.result()
    return job.output_rows or 0
