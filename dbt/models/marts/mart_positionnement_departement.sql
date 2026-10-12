{{
    config(
        partition_by={'field': 'snapshot_date', 'data_type': 'date', 'granularity': 'day'},
        cluster_by=['carburant_code', 'code_departement']
    )
}}

-- Question métier : dans chaque département, Carrefour est-il moins cher ou plus cher
-- que ses concurrents, et de combien ?
-- Seuls les prix frais et les stations sur route (hors autoroute) sont comparés.

with prix_stations as (

    select
        f.snapshot_date,
        f.carburant_code,
        d.code_departement,
        d.departement,
        d.region,
        d.est_carrefour,
        d.type_reseau,
        f.prix
    from {{ ref('fact_prix') }} as f
    inner join {{ ref('dim_station') }} as d using (station_id)
    where f.est_prix_frais
      and d.type_voie = 'R'
      and d.code_departement is not null

),

agrege as (

    select
        snapshot_date,
        carburant_code,
        code_departement,
        any_value(departement) as departement,
        any_value(region) as region,
        countif(est_carrefour) as nb_stations_carrefour,
        countif(not est_carrefour) as nb_stations_concurrentes,
        avg(if(est_carrefour, prix, null)) as prix_moyen_carrefour,
        avg(if(not est_carrefour, prix, null)) as prix_moyen_concurrents,
        avg(if(not est_carrefour and type_reseau = 'Grande distribution', prix, null))
            as prix_moyen_grande_distribution,
        avg(if(type_reseau = 'Pétrolier', prix, null)) as prix_moyen_petroliers
    from prix_stations
    group by snapshot_date, carburant_code, code_departement

)

select
    *,
    round(prix_moyen_carrefour - prix_moyen_concurrents, 4) as ecart_vs_concurrents,
    round(prix_moyen_carrefour - prix_moyen_grande_distribution, 4) as ecart_vs_grande_distribution
from agrege
where nb_stations_carrefour > 0
