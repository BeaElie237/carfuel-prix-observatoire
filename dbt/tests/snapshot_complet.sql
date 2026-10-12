-- Chaque snapshot doit contenir un nombre réaliste de stations avec au moins un prix.
select snapshot_date, count(distinct station_id) as nb_stations
from {{ ref('fact_prix') }}
group by snapshot_date
having count(distinct station_id) < 5000
