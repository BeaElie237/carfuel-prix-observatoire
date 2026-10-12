{{
    config(
        partition_by={'field': 'snapshot_date', 'data_type': 'date', 'granularity': 'day'},
        cluster_by=['carburant_code', 'station_id']
    )
}}

-- Grain : un prix par jour, station et carburant.
-- Reconstruite entièrement à chaque exécution : le bac à sable BigQuery n'autorise pas
-- le DML (MERGE), donc pas de matérialisation incrémentale. À ce volume (environ
-- 50 000 lignes par jour), le coût reste négligeable.

select
    snapshot_date,
    station_id,
    carburant_code,
    prix,
    prix_maj_at,
    jours_depuis_maj,
    jours_depuis_maj <= {{ var('fraicheur_max_jours') }} as est_prix_frais
from {{ ref('stg_prix') }}
where prix between {{ var('prix_min') }} and {{ var('prix_max') }}
