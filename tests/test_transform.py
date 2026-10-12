import json
from datetime import UTC, datetime

from ingestion.transform import (
    csv_enseignes_vers_lignes,
    date_snapshot,
    enregistrements_vers_lignes,
    vers_ndjson,
)

INSTANT = datetime(2026, 10, 12, 22, 30, tzinfo=UTC)  # 00:30 le 13 à Paris


def test_date_snapshot_en_heure_de_paris():
    assert date_snapshot(INSTANT) == "2026-10-13"


def test_une_ligne_par_station_et_payload_intact():
    records = [
        {"id": 91000001, "ville": "Évry", "gazole_prix": 1.659},
        {"id": 91000001, "ville": "doublon"},
        {"id": None, "ville": "sans id"},
        {"id": 75001002, "ville": "Paris"},
    ]
    lignes = enregistrements_vers_lignes(records, INSTANT)
    assert [ligne["station_id"] for ligne in lignes] == ["91000001", "75001002"]
    assert lignes[0]["snapshot_date"] == "2026-10-13"
    assert json.loads(lignes[0]["payload"]) == records[0]


def test_csv_enseignes_virgule_et_point_virgule():
    entete = (
        "id_station_officiel,nom_normalise,adresse,ville,code_postal,"
        "latitude_osm,longitude_osm"
    )
    ligne = '1000002,Carrefour,"16 Avenue de Marboz",Bourg-en-Bresse,01000,46.2185,5.2279'
    for sep in (",", ";"):
        texte = "\ufeff" + (entete + "\n" + ligne + "\n").replace(",", sep)
        resultat = csv_enseignes_vers_lignes(texte, INSTANT)
        assert len(resultat) == 1
        assert resultat[0]["station_id"] == "1000002"
        assert resultat[0]["nom_normalise"] == "Carrefour"
        assert resultat[0]["code_postal"] == "01000"
        assert resultat[0]["latitude_osm"] == 46.2185


def test_csv_enseignes_ignore_les_lignes_incompletes():
    texte = "id_station_officiel,nom_normalise\n,Carrefour\n123,\n456,Total\n"
    assert [x["station_id"] for x in csv_enseignes_vers_lignes(texte, INSTANT)] == ["456"]


def test_ndjson_une_ligne_par_enregistrement():
    contenu = vers_ndjson([{"a": 1}, {"a": "é"}]).decode("utf-8")
    assert contenu.split("\n") == ['{"a": 1}', '{"a": "é"}']
