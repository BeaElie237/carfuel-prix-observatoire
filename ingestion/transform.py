"""Fonctions pures de transformation (testables sans accès réseau ni GCP)."""

import csv
import io
import json
from datetime import datetime
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")


def date_snapshot(instant: datetime) -> str:
    """Date du snapshot en heure de Paris, au format AAAA-MM-JJ."""
    return instant.astimezone(PARIS).date().isoformat()


def enregistrements_vers_lignes(records: list[dict], ingested_at: datetime) -> list[dict]:
    """Une ligne par station : identifiant + enregistrement brut conservé tel quel en JSON.

    Garder le brut rend la couche raw insensible aux changements de schéma de la source :
    le typage se fait ensuite dans dbt (couche staging).
    """
    snapshot = date_snapshot(ingested_at)
    horodatage = ingested_at.isoformat()
    lignes: list[dict] = []
    vus: set[str] = set()
    for rec in records:
        identifiant = rec.get("id")
        if identifiant in (None, ""):
            continue
        station_id = str(identifiant)
        if station_id in vus:
            continue
        vus.add(station_id)
        lignes.append(
            {
                "snapshot_date": snapshot,
                "ingested_at": horodatage,
                "station_id": station_id,
                "payload": json.dumps(rec, ensure_ascii=False, sort_keys=True),
            }
        )
    return lignes


def _flottant(valeur: str | None) -> float | None:
    if valeur is None or valeur.strip() == "":
        return None
    try:
        return float(valeur.replace(",", "."))
    except ValueError:
        return None


def csv_enseignes_vers_lignes(texte: str, loaded_at: datetime) -> list[dict]:
    """Parse le référentiel des enseignes, quel que soit son séparateur (, ou ;)."""
    texte = texte.lstrip("\ufeff")
    premiere_ligne = texte.split("\n", 1)[0]
    separateur = ";" if premiere_ligne.count(";") > premiere_ligne.count(",") else ","
    lecteur = csv.DictReader(io.StringIO(texte), delimiter=separateur)
    horodatage = loaded_at.isoformat()
    lignes: list[dict] = []
    for row in lecteur:
        station_id = (row.get("id_station_officiel") or "").strip()
        nom = (row.get("nom_normalise") or "").strip()
        if not station_id or not nom:
            continue
        lignes.append(
            {
                "station_id": station_id,
                "nom_normalise": nom,
                "adresse": (row.get("adresse") or "").strip() or None,
                "ville": (row.get("ville") or "").strip() or None,
                "code_postal": (row.get("code_postal") or "").strip() or None,
                "latitude_osm": _flottant(row.get("latitude_osm")),
                "longitude_osm": _flottant(row.get("longitude_osm")),
                "loaded_at": horodatage,
            }
        )
    return lignes


def vers_ndjson(lignes: list[dict]) -> bytes:
    return "\n".join(json.dumps(ligne, ensure_ascii=False) for ligne in lignes).encode("utf-8")
