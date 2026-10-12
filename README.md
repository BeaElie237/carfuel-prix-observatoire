# Observatoire des prix des carburants

Pipeline de données sur Google Cloud qui suit chaque jour le prix des carburants dans
toutes les stations-service de France et mesure le positionnement prix des stations
Carrefour face à leurs concurrents.

**Stack** : Python, BigQuery, Cloud Storage, dbt, GitHub Actions, Looker Studio.

## Architecture

```
 Open data (prix)      Open data (enseignes)
        |                      |
        v                      v
   ingestion/extract_prix   ingestion/load_enseignes      Python, lancé par GitHub Actions
        |                      |
        +--> Cloud Storage (brut, optionnel)
        v                      v
   carfuel_raw.prix_snapshots  carfuel_raw.enseignes      BigQuery, couche brute
        |                      |
        v                      v
   stg_prix, stg_stations, stg_enseignes                  dbt, couche staging (vues)
        |
        v
   dim_station, dim_carburant, fact_prix                  dbt, modèle en étoile
        |
        v
   mart_positionnement_departement                        dbt, tables métier
   mart_concurrence_locale
        |
        v
   Looker Studio
```

## Sources

| Donnée | Source | Licence |
| --- | --- | --- |
| Prix par station et carburant | [Prix des carburants en France, flux instantané v2](https://data.economie.gouv.fr/explore/dataset/prix-des-carburants-en-france-flux-instantane-v2/) | Licence Ouverte 2.0 |
| Enseigne de chaque station | [Référentiel des noms et enseignes de stations-service](https://www.data.gouv.fr/datasets/referentiel-des-noms-et-enseignes-de-stations-service-enrichi-par-openstreetmap) | ODbL (OpenStreetMap) |

Le flux officiel ne contient pas la marque des stations : elle vient du second jeu de
données, joint sur l'identifiant officiel du point de vente.

## Choix techniques

- **Couche brute en JSON.** Chaque enregistrement source est stocké tel quel. Si la source
  ajoute ou renomme un champ, l'ingestion ne casse pas : le typage se fait dans dbt.
- **Ingestion idempotente.** Relancer le script le même jour remplace la partition du jour.
- **Partition et clustering.** `fact_prix` est partitionnée par `snapshot_date` et
  clusterisée par carburant et station : un dashboard filtré sur une période ne lit que
  les partitions utiles.
- **Garde-fous.** Le chargement est annulé si le flux contient trop peu de stations, et
  dbt plafonne chaque requête à 1 Go scanné.
- **Pas de MERGE.** Le bac à sable BigQuery n'autorise pas le DML : les tables sont
  reconstruites à chaque exécution, ce qui reste négligeable à ce volume.

## Qualité des données

Tests exécutés à chaque run (`dbt build`) :

- unicité et non-nullité des clés, intégrité référentielle entre faits et dimensions ;
- grain unique de `fact_prix` (jour, station, carburant) ;
- nombre de stations réaliste dans chaque snapshot ;
- alerte si plus de 1 % des prix sortent de la plage plausible ;
- alerte si moins de 70 % des stations ont une enseigne connue ;
- fraîcheur de la source (alerte après 36 h, erreur après 72 h).

## Mise en route

### 1. Projet GCP

1. Créer un projet sur <https://console.cloud.google.com> et noter son identifiant.
2. Ouvrir BigQuery : sans compte de facturation, le projet est en bac à sable (gratuit).
3. Installer le [SDK gcloud](https://cloud.google.com/sdk/docs/install), puis :

```bash
gcloud auth application-default login
gcloud config set project VOTRE_PROJECT_ID
```

### 2. Premier lancement en local

```bash
python -m venv .venv && source .venv/bin/activate    # Windows : .venv\Scripts\activate
pip install -r requirements.txt
export GCP_PROJECT=VOTRE_PROJECT_ID                  # PowerShell : $env:GCP_PROJECT="..."

python -m ingestion.extract_prix       # snapshot du jour -> carfuel_raw.prix_snapshots
python -m ingestion.load_enseignes     # référentiel -> carfuel_raw.enseignes
dbt build --project-dir dbt --profiles-dir dbt
```

### 3. Automatisation avec GitHub Actions

1. Créer un compte de service avec les rôles `BigQuery Data Editor` et `BigQuery Job User` :

```bash
gcloud iam service-accounts create carfuel-pipeline
gcloud projects add-iam-policy-binding VOTRE_PROJECT_ID \
  --member="serviceAccount:carfuel-pipeline@VOTRE_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
gcloud projects add-iam-policy-binding VOTRE_PROJECT_ID \
  --member="serviceAccount:carfuel-pipeline@VOTRE_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=carfuel-pipeline@VOTRE_PROJECT_ID.iam.gserviceaccount.com
```

2. Dans le dépôt GitHub, onglet Settings > Secrets and variables > Actions :
   - secret `GCP_SA_KEY` : le contenu de `sa-key.json` ;
   - variable `GCP_PROJECT` : l'identifiant du projet.
3. Supprimer `sa-key.json` de votre machine. Ce fichier ne doit jamais être commité
   (il est dans `.gitignore`).
4. Lancer le workflow « Pipeline quotidien » à la main (onglet Actions) pour vérifier.

Le pipeline tourne ensuite tous les jours et l'historique se construit jour après jour.

### 4. Cloud Storage (optionnel, demande un compte de facturation)

Créer un bucket, ajouter la variable `GCS_BUCKET` et donner le rôle
`Storage Object Admin` au compte de service : le fichier brut de chaque jour y est archivé.

### 5. Dashboard Looker Studio

Sur <https://lookerstudio.google.com>, créer un rapport avec le connecteur BigQuery sur :

- `mart_positionnement_departement` : carte des départements colorée par
  `ecart_vs_concurrents`, courbe de l'écart dans le temps, filtre par carburant ;
- `mart_concurrence_locale` : part des stations Carrefour les moins chères de leur zone
  (`est_le_moins_cher`), tableau des stations les plus éloignées du prix local.

## Limites connues

- L'historique commence au premier lancement. Le rechargement des archives annuelles
  reste à faire.
- Dans le bac à sable BigQuery, les tables expirent après 60 jours. Activer la
  facturation (le volume reste dans le niveau gratuit) lève cette limite.
- L'enseigne vient d'OpenStreetMap : certaines stations n'en ont pas et sont classées
  « Inconnue ».
- Les ruptures de carburant ne sont pas encore modélisées.
- Les prix sont déclarés par les stations : une valeur peut être erronée ou périmée,
  d'où les filtres de plausibilité et de fraîcheur.
