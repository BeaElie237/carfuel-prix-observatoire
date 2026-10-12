"""Configuration lue depuis les variables d'environnement."""

import os

# Flux instantané officiel (toutes les stations de France, mis à jour en continu).
PRIX_EXPORT_URL = (
    "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "prix-des-carburants-en-france-flux-instantane-v2/exports/json"
)

# Référentiel id officiel -> enseigne (le flux officiel ne contient pas la marque).
# Source : data.gouv.fr, enrichi par OpenStreetMap, licence ODbL.
ENSEIGNES_CSV_URL = (
    "https://www.data.gouv.fr/api/1/datasets/r/0207ded0-2d19-47af-b1a6-62915ec1b721"
)

GCP_PROJECT = os.environ.get("GCP_PROJECT", "")
BQ_LOCATION = os.environ.get("BQ_LOCATION", "EU")
BQ_RAW_DATASET = os.environ.get("BQ_RAW_DATASET", "carfuel_raw")

# Optionnel : si renseigné, le fichier brut du jour est aussi archivé dans Cloud Storage.
GCS_BUCKET = os.environ.get("GCS_BUCKET", "")

# Garde-fou qualité : le flux contient environ 10 000 stations.
MIN_STATIONS_ATTENDUES = int(os.environ.get("MIN_STATIONS_ATTENDUES", "5000"))


def exiger_projet() -> str:
    if not GCP_PROJECT:
        raise SystemExit("Variable d'environnement GCP_PROJECT manquante.")
    return GCP_PROJECT
