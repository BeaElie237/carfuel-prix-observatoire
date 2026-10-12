-- Une ligne par snapshot, station et carburant (dépivotage du flux source).
-- Le filtre sur snapshot_date dans les modèles en aval profite de la partition de la table brute.

with source as (

    select snapshot_date, station_id, payload
    from {{ source('raw', 'prix_snapshots') }}

),

depivote as (

    {% for champ, code, libelle in liste_carburants() %}
    select
        snapshot_date,
        station_id,
        '{{ code }}' as carburant_code,
        safe_cast(json_value(payload, '$.{{ champ }}_prix') as float64) as prix,
        safe_cast(json_value(payload, '$.{{ champ }}_maj') as timestamp) as prix_maj_at
    from source
    {% if not loop.last %}union all{% endif %}
    {% endfor %}

)

select
    snapshot_date,
    station_id,
    carburant_code,
    prix,
    prix_maj_at,
    date_diff(snapshot_date, date(prix_maj_at, 'Europe/Paris'), day) as jours_depuis_maj
from depivote
where prix is not null
