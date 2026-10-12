{{ config(cluster_by=['code_departement', 'groupe_enseigne']) }}

select
    s.station_id,
    coalesce(e.enseigne, 'Inconnue') as enseigne,
    coalesce(e.groupe_enseigne, 'Inconnue') as groupe_enseigne,
    coalesce(e.groupe_enseigne = 'Carrefour', false) as est_carrefour,
    case
        when e.groupe_enseigne in (
            'Carrefour', 'E.Leclerc', 'Intermarché', 'Auchan', 'Système U', 'Casino', 'Cora'
        ) then 'Grande distribution'
        when e.groupe_enseigne is null then 'Inconnu'
        when e.groupe_enseigne = 'Autres' then 'Autres'
        else 'Pétrolier'
    end as type_reseau,
    s.adresse,
    s.ville,
    s.code_postal,
    s.code_departement,
    s.departement,
    s.region,
    s.type_voie,
    s.latitude,
    s.longitude,
    s.position,
    s.derniere_presence
from {{ ref('stg_stations') }} as s
left join {{ ref('stg_enseignes') }} as e using (station_id)
