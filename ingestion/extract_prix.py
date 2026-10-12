"""Extrait le flux instantané des prix et charge le snapshot du jour dans BigQuery.

Idempotent : relancer le script le même jour remplace la partition du jour.

    python -m ingestion.extract_prix
"""

import gzip
import json
import logging
import time
from datetime import UTC, datetime

import requests
from google.cloud import bigquery, storage

from ingestion import bq, config
from ingestion.transform import date_snapshot, enregistrements_vers_lignes

log = logging.getLogger("extract_prix")

SCHEMA = [
    bigquery.SchemaField("snapshot_date", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("station_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("payload", "STRING", mode="REQUIRED"),
]


def telecharger() -> list[dict]:
    reponse = requests.get(config.PRIX_EXPORT_URL, timeout=300)
    reponse.raise_for_status()
    records = reponse.json()
    if not isinstance(records, list):
        raise ValueError("Format inattendu : le flux devrait être une liste JSON.")
    return records


def telecharger_complet(tentatives: int = 6, attente_s: int = 60) -> list[dict]:
    """Retélécharge tant que le flux est incomplet.

    Le flux est republié toutes les quelques minutes ; pendant une republication,
    l'export peut ne renvoyer qu'une partie des stations.
    """
    records: list[dict] = []
    for essai in range(1, tentatives + 1):
        try:
            records = telecharger()
        except (requests.RequestException, ValueError) as erreur:
            log.warning("Essai %d/%d : échec du téléchargement (%s)", essai, tentatives, erreur)
            records = []
        else:
            log.info("Essai %d/%d : %d enregistrements", essai, tentatives, len(records))
            if len(records) >= config.MIN_STATIONS_ATTENDUES:
                return records
        if essai < tentatives:
            log.info("Flux incomplet, nouvel essai dans %d s", attente_s)
            time.sleep(attente_s)
    return records


def archiver_gcs(records: list[dict], snapshot: str) -> None:
    """Archive le brut dans Cloud Storage (data lake), si un bucket est configuré."""
    blob = (
        storage.Client(project=config.exiger_projet())
        .bucket(config.GCS_BUCKET)
        .blob(f"prix_carburants/snapshot_date={snapshot}/flux_instantane.json.gz")
    )
    contenu = gzip.compress(json.dumps(records, ensure_ascii=False).encode("utf-8"))
    blob.upload_from_string(contenu, content_type="application/gzip")
    log.info("Brut archivé : gs://%s/%s", config.GCS_BUCKET, blob.name)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    maintenant = datetime.now(UTC)
    snapshot = date_snapshot(maintenant)

    records = telecharger_complet()

    lignes = enregistrements_vers_lignes(records, maintenant)
    if len(lignes) < config.MIN_STATIONS_ATTENDUES:
        raise SystemExit(
            f"Seulement {len(lignes)} stations reçues "
            f"(minimum attendu : {config.MIN_STATIONS_ATTENDUES}). Chargement annulé."
        )

    if config.GCS_BUCKET:
        archiver_gcs(records, snapshot)

    client = bq.client()
    bq.creer_dataset_si_absent(client, config.BQ_RAW_DATASET)
    partition = snapshot.replace("-", "")
    destination = f"{client.project}.{config.BQ_RAW_DATASET}.prix_snapshots${partition}"
    nb = bq.charger(client, lignes, destination, SCHEMA, partition_field="snapshot_date")
    log.info("%d lignes chargées dans %s", nb, destination)


if __name__ == "__main__":
    main()
