CAMPAIGNS_QUERY = """
WITH map_fuente AS (
  SELECT 'FDA' AS clave, 'nest'         AS fuente UNION ALL
  SELECT 'DQ'  AS clave, 'api-nest-dq'  AS fuente UNION ALL
  SELECT 'FAB' AS clave, 'api-nest-fab' AS fuente UNION ALL
  SELECT 'YZA' AS clave, 'api-nest-yza' AS fuente UNION ALL
  SELECT 'TH'  AS clave, 'api-nest-th'  AS fuente UNION ALL
  SELECT 'MK'  AS clave, 'api-nest-mk'  AS fuente
),
src AS (
  SELECT 'nest'          AS fuente, id, nombre, id_compania FROM `nest`.campanas UNION ALL
  SELECT 'api-nest-dq'   AS fuente, id, nombre, id_compania FROM `api-nest-dq`.campanas UNION ALL
  SELECT 'api-nest-fab'  AS fuente, id, nombre, id_compania FROM `api-nest-fab`.campanas UNION ALL
  SELECT 'api-nest-yza'  AS fuente, id, nombre, id_compania FROM `api-nest-yza`.campanas UNION ALL
  SELECT 'api-nest-th'   AS fuente, id, nombre, id_compania FROM `api-nest-th`.campanas UNION ALL
  SELECT 'api-nest-mk'   AS fuente, id, nombre, id_compania FROM `api-nest-mk`.campanas
)
SELECT
    c.id              AS claw_id,
    c.active          AS activo_claw,
    comp.clave        AS cliente,
    comp.nombre       AS nombre_cliente,
    c.created_at      AS inicio_campana,
    c.nombre          AS nombre_campana_claw,
    c.id_campana_nest,
    s.id              AS nest_id,
    s.nombre          AS nombre_campana_nest,
    s.id_compania     AS id_compania_nest,
    s.fuente          AS fuente_nest
FROM `api-claw`.campanas   AS c
JOIN `api-claw`.companias  AS comp ON comp.id = c.id_compania
JOIN map_fuente             AS mf  ON mf.clave = comp.clave
JOIN src                    AS s   ON s.fuente = mf.fuente AND s.id = c.id_campana_nest;
"""


def get_campaigns(conn):
    return conn.query(CAMPAIGNS_QUERY, ttl=0)
