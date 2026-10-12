{{ config(severity='warn') }}
-- Alerte si moins de 70 % des stations ont une enseigne connue :
-- les comparaisons Carrefour / concurrents deviendraient peu fiables.
with couverture as (
    select
        countif(groupe_enseigne != 'Inconnue') as nb_connues,
        count(*) as nb_total
    from {{ ref('dim_station') }}
)
select * from couverture
where safe_divide(nb_connues, nb_total) < 0.7
