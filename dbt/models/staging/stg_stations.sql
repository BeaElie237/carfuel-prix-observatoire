-- Attributs de chaque station, pris dans son snapshot le plus récent.

with source as (

    select
        station_id,
        snapshot_date,
        payload,
        row_number() over (partition by station_id order by snapshot_date desc) as rang
    from {{ source('raw', 'prix_snapshots') }}

),

dernier as (

    select * from source where rang = 1

),

type as (

    select
        station_id,
        snapshot_date as derniere_presence,
        json_value(payload, '$.adresse') as adresse,
        json_value(payload, '$.ville') as ville,
        json_value(payload, '$.cp') as code_postal,
        json_value(payload, '$.code_departement') as code_departement,
        json_value(payload, '$.departement') as departement,
        json_value(payload, '$.region') as region,
        -- 'R' = route, 'A' = autoroute
        json_value(payload, '$.pop') as type_voie,
        -- Coordonnées : objet geom si présent, sinon champs latitude/longitude (en 1/100 000 de degré)
        coalesce(
            safe_cast(json_value(payload, '$.geom.lat') as float64),
            safe_cast(json_value(payload, '$.latitude') as float64) / 100000
        ) as latitude,
        coalesce(
            safe_cast(json_value(payload, '$.geom.lon') as float64),
            safe_cast(json_value(payload, '$.longitude') as float64) / 100000
        ) as longitude
    from dernier

)

select
    *,
    case
        when latitude between -90 and 90 and longitude between -180 and 180
            then st_geogpoint(longitude, latitude)
    end as position
from type
