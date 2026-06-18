# Generador de carpetas de campaña

App de Streamlit que lee campañas desde MySQL y genera/reusa en Google Drive la estructura de carpetas año → campaña → subcarpetas.

## Setup local

1. Instalar dependencias:

   ```
   pip install -r requirements.txt
   ```

2. Copiar la plantilla de secrets y llenarla con credenciales reales:

   ```
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

   Editar `.streamlit/secrets.toml` con:
   - `app_password`: la contraseña de acceso a la app.
   - `[connections.mysql]`: credenciales de la base de datos MySQL (DigitalOcean).
   - `[gcp_service_account]`: el JSON completo de la service account de Google (Drive API habilitada).

3. Compartir las 4 carpetas raíz de Drive (FDA, FAB, DQ, YZA) con el `client_email` de la service account, como Editor.

4. Correr las pruebas:

   ```
   pytest -v
   ```

5. Correr la app:

   ```
   streamlit run app.py
   ```

## Deploy en Streamlit Community Cloud

1. Subir el repo a GitHub (incluye `.env`, que solo contiene IDs de carpetas de Drive, no es sensible).
2. Crear la app en [share.streamlit.io](https://share.streamlit.io) apuntando al repo y a `app.py`.
3. En *Settings → Secrets* de la app, pegar el contenido completo de tu `.streamlit/secrets.toml` local (con los valores reales).
4. Verificar el flujo completo contra la URL pública: login, selección de cliente/campaña, generación de carpetas, y el caso de carpeta de campaña ya existente (Reusar/Crear nueva).

## Clientes sin carpeta raíz configurada

Las claves `TH` y `MK` existen en los datos de campañas pero aún no tienen carpeta raíz en `.env`. Si se selecciona una campaña de esos clientes, la app muestra un error (`No hay carpeta raíz configurada para el cliente 'TH'.`) sin tocar Drive. Para habilitarlos, agregar `DRIVE_ROOT_TH` / `DRIVE_ROOT_MK` a `.env` y su mapeo en `config.py`.
