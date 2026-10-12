{{ config(cluster_by=['carburant_code', 'code_departement']) }}

-- Question métier : pour chaque station Carrefour, où se situe son prix par rapport
-- aux stations concurrentes dans un rayon de {{ var('rayon_concurrence_m') }} m ?
-- Calculé sur le dernier snapshot uniquement.

with dernier_jour as (

    select max(snapshot_date) as snapshot_date from {{ ref('fact_prix') }}

),

prix_du_jour as (

    select
        f.snapshot_date,
        f.station_id,
        f.carburant_code,
        f.prix,
        d.est_carrefour,
        d.groupe_enseigne,
        d.enseigne,
        d.ville,
        d.code_departement,
        d.position
    from {{ ref('fact_prix') }} as f
    inner join dernier_jour using (snapshot_date)
    inner join {{ ref('dim_station') }} as d using (station_id)
    where f.est_prix_frais
      and d.position is not null

),

paires as (

    select
        c.snapshot_date,
        c.station_id,
        c.enseigne,
        c.ville,
        c.code_departement,
        c.carburant_code,
        c.prix as prix_carrefour,
        v.station_id as concurrent_id,
        v.groupe_enseigne as concurrent_groupe,
        v.prix as prix_concurrent
    from prix_du_jour as c
    inner join prix_du_jour as v
        on c.carburant_code = v.carburant_code
        and not v.est_carrefour
        and st_dwithin(c.position, v.position, {{ var('rayon_concurrence_m') }})
    where c.est_carrefour

)

select
    snapshot_date,
    station_id,
    any_value(enseigne) as enseigne,
    any_value(ville) as ville,
    any_value(code_departement) as code_departement,
    carburant_code,
    any_value(prix_carrefour) as prix_carrefour,
    count(*) as nb_concurrents,
    round(avg(prix_concurrent), 4) as prix_moyen_concurrents,
    min(prix_concurrent) as prix_min_concurrents,
    round(any_value(prix_carrefour) - avg(prix_concurrent), 4) as ecart_vs_moyenne,
    round(any_value(prix_carrefour) - min(prix_concurrent), 4) as ecart_vs_moins_cher,
    -- Rang 1 = Carrefour est le moins cher de sa zone
    1 + countif(prix_concurrent < prix_carrefour) as rang_prix,
    any_value(prix_carrefour) <= min(prix_concurrent) as est_le_moins_cher,
    array_agg(concurrent_groupe order by prix_concurrent limit 1)[offset(0)] as groupe_le_moins_cher
from paires
group by snapshot_date, station_id, carburant_code
