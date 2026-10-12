"""Charge le référentiel des enseignes (id officiel de station -> marque) dans BigQuery.

    python -m ingestion.load_enseignes
"""

import logging
from datetime import UTC, datetime

import requests
from google.cloud import bigquery

from ingestion import bq, config
from ingestion.transform import csv_enseignes_vers_lignes

log = logging.getLogger("load_enseignes")

SCHEMA = [
    bigquery.SchemaField("station_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("nom_normalise", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("adresse", "STRING"),
    bigquery.SchemaField("ville", "STRING"),
    bigquery.SchemaField("code_postal", "STRING"),
    bigquery.SchemaField("latitude_osm", "FLOAT"),
    bigquery.SchemaField("longitude_osm", "FLOAT"),
    bigquery.SchemaField("loaded_at", "TIMESTAMP", mode="REQUIRED"),
]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    reponse = requests.get(config.ENSEIGNES_CSV_URL, timeout=120)
    reponse.raise_for_status()
    reponse.encoding = "utf-8"

    lignes = csv_enseignes_vers_lignes(reponse.text, datetime.now(UTC))
    if len(lignes) < 1000:
        raise SystemExit(f"Référentiel anormalement petit ({len(lignes)} lignes). Annulé.")

    client = bq.client()
    bq.creer_dataset_si_absent(client, config.BQ_RAW_DATASET)
    destination = f"{client.project}.{config.BQ_RAW_DATASET}.enseignes"
    nb = bq.charger(client, lignes, destination, SCHEMA)
    log.info("%d enseignes chargées dans %s", nb, destination)


if __name__ == "__main__":
    main()
