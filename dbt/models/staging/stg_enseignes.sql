-- Enseigne de chaque station, regroupée par groupe de distribution.

with source as (

    select
        station_id,
        trim(nom_normalise) as enseigne,
        lower(trim(nom_normalise)) as enseigne_min
    from {{ source('raw', 'enseignes') }}

)

select
    station_id,
    enseigne,
    case
        when regexp_contains(enseigne_min, r'carrefour') then 'Carrefour'
        when regexp_contains(enseigne_min, r'leclerc') then 'E.Leclerc'
        when regexp_contains(enseigne_min, r'intermarch|netto') then 'Intermarché'
        when regexp_contains(enseigne_min, r'auchan') then 'Auchan'
        when regexp_contains(enseigne_min, r'(super|hyper|march[ée]|station|syst[èe]me) u\b|\bu express')
            then 'Système U'
        when regexp_contains(enseigne_min, r'casino|g[ée]ant') then 'Casino'
        when regexp_contains(enseigne_min, r'cora') then 'Cora'
        when regexp_contains(enseigne_min, r'total|elan\b|\belf\b') then 'TotalEnergies'
        when regexp_contains(enseigne_min, r'esso') then 'Esso'
        when regexp_contains(enseigne_min, r'\bbp\b') then 'BP'
        when regexp_contains(enseigne_min, r'avia') then 'Avia'
        when regexp_contains(enseigne_min, r'shell') then 'Shell'
        when regexp_contains(enseigne_min, r'eni|agip') then 'Eni'
        else 'Autres'
    end as groupe_enseigne
from source
