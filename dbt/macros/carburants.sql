{# Liste des carburants : (préfixe du champ dans la source, code, libellé) #}
{% macro liste_carburants() %}
  {{ return([
    ('gazole', 'GAZOLE', 'Gazole'),
    ('sp95', 'SP95', 'Sans plomb 95'),
    ('e10', 'E10', 'Sans plomb 95-E10'),
    ('sp98', 'SP98', 'Sans plomb 98'),
    ('e85', 'E85', 'Superéthanol E85'),
    ('gplc', 'GPLC', 'GPL carburant'),
  ]) }}
{% endmacro %}
