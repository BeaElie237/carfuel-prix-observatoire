-- Le grain de la table de faits doit être unique : jour x station x carburant.
select snapshot_date, station_id, carburant_code, count(*) as nb
from {{ ref('fact_prix') }}
group by 1, 2, 3
having count(*) > 1
