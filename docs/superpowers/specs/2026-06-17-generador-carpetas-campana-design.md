# Generador de carpetas de campaña — Diseño

**Fecha:** 2026-06-17
**Estado:** Aprobado por el usuario, pendiente de plan de implementación.

## Propósito

App de Streamlit que, a partir de datos de campañas extraídos de MySQL (DigitalOcean), genera en Google Drive la estructura de carpetas de una campaña seleccionada por el usuario: año → campaña → subcarpetas de trabajo. Reemplaza la creación manual de estas carpetas.

## Fuente de datos: query SQL

Se ejecuta el siguiente query contra MySQL (motor MySQL alojado en DigitalOcean, credenciales ya disponibles):

```sql
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
```

Columnas relevantes para esta app: `cliente` (clave corta, ej. `FDA`), `nombre_cliente` (nombre largo, ej. `Farmacias del ahorro`), `nombre_campana_claw` (nombre exacto que se usa como nombre de carpeta de campaña), `activo_claw`.

Un archivo de ejemplo con datos reales de salida de este query vive en la raíz del repo: `Ejemplo Query.json` (182 filas de muestra). Se usa como fixture de pruebas.

**Dato de diseño importante:** existen filas con el mismo `(cliente, nombre_campana_claw)` pero distinto `claw_id` (4 casos detectados en la muestra, ej. `FDA JUN24 - 1` aparece 2 veces para FDA). Como el nombre de la carpeta depende únicamente de `nombre_campana_claw`, esto no es ambiguo para efectos de generación de carpetas — el dropdown de campañas se deduplica por nombre.

`map_fuente` contempla 6 claves de cliente (`FDA`, `DQ`, `FAB`, `YZA`, `TH`, `MK`), pero por ahora solo 4 tienen carpeta raíz de Drive configurada (ver sección Config). Si aparece una campaña con clave `TH` o `MK` en el dropdown, la app debe fallar con un error claro al intentar resolver su carpeta raíz, no silenciosamente.

## Flujo funcional

1. **Gate de contraseña** — input de password comparado contra `st.secrets["app_password"]`. Si no coincide, no se renderiza nada más de la app.
2. **Carga de campañas** — al iniciar la sesión (y al pulsar el botón "🔄 Refrescar campañas de Claw"), se ejecuta el query de arriba y el resultado (DataFrame) se guarda en `st.session_state`. No hay cache con TTL; la única forma de obtener datos nuevos es ese botón explícito.
3. **Dropdown de cliente** — valores únicos de `nombre_cliente` presentes en el DataFrame cargado.
4. **Dropdown de campaña** — valores únicos de `nombre_campana_claw` filtrados por el cliente seleccionado (deduplicados, sin filtrar por `activo_claw`: se muestran todas las campañas, activas e inactivas). De la fila seleccionada se obtiene también `cliente` (la clave corta).
5. **Selector de año** — `number_input` cuyo valor por defecto es el año del **mes siguiente** al mes actual (ej. en agosto 2026 el default es 2026; en diciembre 2026 el default es 2027, porque enero ya cae en 2027). El usuario puede cambiarlo.
6. **Carpetas extra (opcional)** — campo de texto donde el usuario puede escribir nombres de carpetas adicionales (separados por coma) que se crearán junto con las 5 por defecto, **solo para esta ejecución** — no se guardan ni modifican los secrets.
7. **Botón "Generar"**:
   - Resuelve el ID de carpeta raíz de Drive según la clave de cliente (`.env`). Si no existe el mapeo, `st.error` y se detiene sin tocar Drive.
   - Construye una vista previa del árbol de carpetas que se va a tocar, **sin crear nada todavía**:
     - Nivel 1 (año): busca `"{cliente} {año}"` (ej. `"FDA 2026"`) dentro de la carpeta raíz del cliente. Es informativo solamente — no se le pregunta nada al usuario; si existe se reusa, si no existe se crea.
     - Nivel 2 (campaña): busca `nombre_campana_claw` dentro de la carpeta de año (solo se busca si el nivel 1 ya existía; si la carpeta de año no existe, el nivel 2 se marca directamente como "se creará", sin llamada a Drive). **Este es el único nivel interactivo**: si ya existe, se le pregunta al usuario Reusar / Crear nueva.
     - Nivel 3 (subcarpetas): las 5 subcarpetas por defecto (`Fotos`, `Totales`, `Distribución`, `Tipos de Caja`, `Acomodo`, configurables desde secrets) + las carpetas extra ingresadas en el paso 6, dentro de la carpeta de campaña que resulte del nivel 2. Igual que el nivel 1, es informativo: si ya existen se reusan, si no existen se crean — sin preguntar nada (si se reusa la carpeta de campaña existente, se asume que esas subcarpetas ya están ahí; si falta alguna, simplemente se crea la que falte).
   - El resultado de esta vista previa (existencia + IDs encontrados) se guarda en `st.session_state` para no repetir las búsquedas en Drive en cada re-render posterior.
8. **Resolución de conflicto de campaña** — se muestra únicamente si la carpeta de campaña (nivel 2) ya existe:
   - Selector Reusar / Crear nueva, con "Reusar" como opción por defecto.
   - Si el usuario elige "Crear nueva", aparece un campo de texto con el nombre de la carpeta a crear, precargado con `nombre_campana_claw` (el mismo nombre de la campaña) pero editable — el usuario puede modificarlo antes de confirmar, y ese es el nombre que se usará para la carpeta nueva.
   - Cambiar este selector o el nombre editado solo actualiza el estado en `session_state`, no vuelve a consultar Drive.
9. **Botón "Confirmar y crear"** — recorre el árbol de arriba hacia abajo: crea/reusa el año automáticamente, crea/reusa la campaña según la decisión del paso 8 (usando el nombre editado si se eligió "Crear nueva"), y crea/reusa cada subcarpeta de nivel 3 automáticamente dentro de la carpeta de campaña resultante. Esto ocurre una sola vez, al pulsar el botón.
10. **Resumen final** — tabla con cada carpeta tocada (nombre, acción tomada) + un link directo y clicable a la carpeta de la campaña (nivel 2) en Drive.

## Estructura de Drive (referencia visual)

Dentro de la carpeta raíz de cada cliente, las carpetas de año son hijas directas con el patrón `"{cliente} {año}"` (ej. `FDA 2026`, `FDA 2025`, `FDA 2024`, ...). Esto es igual para los 4 clientes configurados.

## Arquitectura y componentes

```
app.py                  → orquesta la UI y el flujo end-to-end
config.py               → carga .env (IDs de carpetas raíz por cliente) y constantes desde secrets
sql_service.py          → ejecuta el query de campañas vía st.connection, devuelve DataFrame
drive_service.py        → wrapper de la API de Google Drive
folder_planner.py       → lógica de planeación del árbol de carpetas (año/campaña/subcarpetas)
```

- **`sql_service.get_campaigns()`** — usa `st.connection("mysql", type="sql")` (SQLAlchemy vía Streamlit, credenciales en `secrets.toml`), corre el query y devuelve un DataFrame con las columnas descritas arriba.
- **`drive_service`** — usa `google-api-python-client` + `google-auth`, autenticado con la service account cuyo JSON vive en `st.secrets["gcp_service_account"]`. Expone:
  - `build_client()` — crea el cliente autenticado de la API.
  - `find_child_folder(client, parent_id, name)` — busca una carpeta por nombre exacto dentro de un padre; devuelve su ID o `None`.
  - `create_folder(client, parent_id, name)` — crea la carpeta y devuelve su ID.
  - `get_folder_link(folder_id)` — arma la URL pública de Drive para esa carpeta.
- **`folder_planner.compute_default_year(today)`** — función pura: año del mes siguiente a `today`.
- **`folder_planner.build_preview(drive_client, root_id, año, nombre_campaña, subcarpetas)`** — recorre la jerarquía llamando a `find_child_folder` solo cuando el padre del nivel ya existe; devuelve una lista de nodos `{nivel, nombre, existe, folder_id}`. Solo el nodo de nivel "campaña" es interactivo (requiere decisión Reusar/Crear nueva + nombre editable si aplica); año y subcarpetas se resuelven automáticamente (reusar si existen, crear si no) sin intervención del usuario.

## Configuración: `.env` vs Streamlit secrets

**`.env`** (commiteado al repo — no contiene datos sensibles, solo IDs de carpetas de Drive que ya están compartidas con la service account):
```
DRIVE_ROOT_FDA=<id de carpeta>
DRIVE_ROOT_FAB=<id de carpeta>
DRIVE_ROOT_DQ=<id de carpeta>
DRIVE_ROOT_YZA=<id de carpeta>
```
Debe quedar commiteado (no en `.gitignore`) porque Streamlit Community Cloud solo despliega lo que está en el repo; no hay forma de "subir" un `.env` aparte en el dashboard.

**`secrets.toml`** (sensible — local en `.streamlit/secrets.toml`, gitignorado; en producción se pega el mismo contenido en el panel *Settings → Secrets* de Streamlit Community Cloud):
```toml
app_password = "..."

default_subfolders = ["Fotos", "Totales", "Distribución", "Tipos de Caja", "Acomodo"]

[connections.mysql]
dialect = "mysql"
host = "..."
port = 3306
database = "..."
username = "..."
password = "..."

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
# ...resto de campos estándar del JSON de service account
```

La service account debe tener acceso compartido (como editor) a las 4 carpetas raíz de Drive.

## Manejo de errores

- **Falla la conexión a MySQL** → `st.error` ("No se pudo conectar a la base de datos") y se detiene; no se muestran dropdowns.
- **Clave de cliente sin carpeta raíz mapeada en `.env`** (caso actual de `TH`/`MK`, o cualquier clave futura sin configurar) → `st.error` específico nombrando la clave faltante, antes de cualquier llamada a Drive.
- **Falla la API de Drive al crear un nodo puntual** (permisos, rate limit, red) → se captura por nodo individual: se detiene esa rama del árbol, se muestra en el resumen qué se alcanzó a crear/reusar y cuál fue el primer fallo. No se intenta deshacer lo ya creado (Drive no tiene rollback transaccional y no aporta valor borrar carpetas ya creadas correctamente).
- **Carpetas extra repetidas, vacías o con espacios de más** en el input de texto → se normalizan (trim) y deduplican antes de construir el árbol.
- **Contraseña incorrecta** → `st.error` genérico sin pistas sobre la contraseña correcta.

## Rendimiento y comportamiento de Streamlit

Streamlit re-ejecuta el script completo en cada interacción del usuario (modelo normal del framework), pero esto **no implica** repetir operaciones costosas:
- El DataFrame de campañas vive en `st.session_state`; solo se recarga con el botón explícito de refrescar.
- El árbol de vista previa (resultado de las búsquedas en Drive) también vive en `st.session_state` tras pulsar "Generar"; cambiar un selector Reusar/Crear nueva en la tabla solo actualiza ese campo en memoria, sin volver a consultar Drive.
- La creación real de carpetas en Drive solo ocurre al pulsar "Confirmar y crear", una única vez por ejecución.

## Pruebas

- **`folder_planner` (lógica pura)** con pytest:
  - `compute_default_year()` cubriendo el caso límite de cambio de año (diciembre → enero del año siguiente).
  - `build_preview()` con un `drive_client` simulado (mock), verificando que no se consulta un nivel si su padre no existe.
- **Procesamiento del DataFrame de campañas** usando `Ejemplo Query.json` como fixture: validar que el dropdown de campañas deduplica correctamente nombres repetidos para un mismo cliente.
- **MySQL y Google Drive son servicios externos reales** — no se mockean en un pipeline de CI automatizado. La verificación de integración es manual antes de cada deploy: correr `streamlit run app.py` localmente, generar una carpeta de prueba en una campaña de sandbox, y confirmar en Drive que la estructura, nombres y links son correctos.

## Fuera de alcance (explícitamente no incluido en este diseño)

- Carpetas raíz de Drive para los clientes `TH` y `MK` (se agregarán a `.env` cuando existan).
- Persistencia de carpetas extra agregadas manualmente como nuevas opciones por defecto (es una decisión explícita: solo aplican a la ejecución actual).
- Cache de resultados del query SQL con TTL (decisión explícita: siempre fresco, con botón de refresco manual).
- Autenticación de Drive vía OAuth de usuario (se usa exclusivamente service account).
