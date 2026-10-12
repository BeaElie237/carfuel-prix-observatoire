{% for champ, code, libelle in liste_carburants() %}
select '{{ code }}' as carburant_code, '{{ libelle }}' as carburant_libelle
{% if not loop.last %}union all{% endif %}
{% endfor %}
