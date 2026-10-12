{{ config(severity='warn') }}
-- Alerte si plus de 1 % des prix d'un snapshot sortent de la plage plausible :
-- signe d'un changement de format ou d'unité dans la source.
select
    snapshot_date,
    countif(prix not between {{ var('prix_min') }} and {{ var('prix_max') }}) as nb_aberrants,
    count(*) as nb_total
from {{ ref('stg_prix') }}
group by snapshot_date
having safe_divide(nb_aberrants, nb_total) > 0.01
