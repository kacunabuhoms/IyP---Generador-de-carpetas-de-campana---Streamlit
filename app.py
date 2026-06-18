from datetime import date

import streamlit as st
from dotenv import load_dotenv

import campaign_data
import config
import drive_service
import folder_planner
import sql_service

load_dotenv()

st.set_page_config(page_title="Generador de carpetas de campana", page_icon="📁")


def _gate_de_contrasena() -> bool:
    if st.session_state.get("autenticado"):
        return True
    contrasena = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if contrasena == config.get_app_password():
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    return False


def _cargar_campanas(conn) -> bool:
    try:
        st.session_state["campanas_df"] = sql_service.get_campaigns(conn)
        return True
    except Exception:
        st.error("No se pudo conectar a la base de datos.")
        return False


def _parsear_carpetas_extra(texto: str) -> list[str]:
    nombres = [parte.strip() for parte in texto.split(",")]
    nombres_unicos: list[str] = []
    for nombre in nombres:
        if nombre and nombre not in nombres_unicos:
            nombres_unicos.append(nombre)
    return nombres_unicos


def _mostrar_resumen(resultado) -> None:
    st.subheader("Resumen")
    if resultado.error:
        st.error(resultado.error)
    st.table(resultado.items)
    if resultado.campana_folder_id:
        link = drive_service.get_folder_link(resultado.campana_folder_id)
        st.markdown(f"[Abrir carpeta de campaña en Drive]({link})")


def _mostrar_vista_previa_y_confirmar(preview) -> None:
    st.subheader("Vista previa")
    st.write(
        f"Año: **{preview.anio.nombre}** — "
        f"{'ya existe, se reusará' if preview.anio.existe else 'se creará'}"
    )

    if preview.campana.existe:
        accion = st.radio(
            f"La carpeta de campaña '{preview.campana.nombre}' ya existe. ¿Qué hacer?",
            options=["reusar", "crear_nueva"],
            format_func=lambda v: "Reusar la existente" if v == "reusar" else "Crear una nueva",
            key="decision_accion",
        )
        nombre_final = preview.campana.nombre
        if accion == "crear_nueva":
            nombre_final = st.text_input(
                "Nombre de la nueva carpeta de campaña",
                value=preview.campana.nombre,
                key="decision_nombre",
            )
    else:
        accion = "crear_nueva"
        nombre_final = preview.campana.nombre
        st.write(f"Campaña: **{nombre_final}** — se creará")

    subcarpetas = config.get_default_subfolders() + st.session_state.get("carpetas_extra", [])

    if st.button("Confirmar y crear"):
        drive = drive_service.build_client()
        decision = folder_planner.CampanaDecision(accion=accion, nombre_final=nombre_final)
        resultado = folder_planner.execute_plan(
            drive=drive,
            root_id=st.session_state["root_id"],
            preview=preview,
            decision=decision,
            subfolder_names=subcarpetas,
        )
        st.session_state["resultado_ejecucion"] = resultado

    resultado = st.session_state.get("resultado_ejecucion")
    if resultado is not None:
        _mostrar_resumen(resultado)


def main() -> None:
    st.title("Generador de carpetas de campaña")

    if not _gate_de_contrasena():
        return

    conn = st.connection("mysql", type="sql")

    if "campanas_df" not in st.session_state:
        if not _cargar_campanas(conn):
            return

    if st.button("🔄 Refrescar campañas de Claw"):
        if _cargar_campanas(conn):
            st.session_state.pop("preview", None)
            st.session_state.pop("resultado_ejecucion", None)

    df = st.session_state["campanas_df"]

    clientes = campaign_data.unique_clients(df)
    nombre_cliente = st.selectbox("Cliente", clientes)

    campanas_cliente = campaign_data.campaigns_for_client(df, nombre_cliente)
    nombre_campana = st.selectbox("Campaña", campanas_cliente["nombre_campana_claw"].tolist())

    fila_campana = campanas_cliente[campanas_cliente["nombre_campana_claw"] == nombre_campana].iloc[0]
    cliente_clave = fila_campana["cliente"]

    anio_default = folder_planner.compute_default_year(date.today())
    anio = st.number_input("Año", min_value=2000, max_value=2100, value=anio_default, step=1)

    carpetas_extra_texto = st.text_input("Carpetas extra (separadas por coma, opcional)")
    carpetas_extra = _parsear_carpetas_extra(carpetas_extra_texto)

    if st.button("Generar"):
        root_id = config.get_drive_root_id(cliente_clave)
        if root_id is None:
            st.error(f"No hay carpeta raíz configurada para el cliente '{cliente_clave}'.")
            return
        drive = drive_service.build_client()
        preview = folder_planner.build_preview(
            drive=drive,
            root_id=root_id,
            cliente=cliente_clave,
            anio=int(anio),
            nombre_campana=nombre_campana,
        )
        st.session_state["preview"] = preview
        st.session_state["root_id"] = root_id
        st.session_state["carpetas_extra"] = carpetas_extra
        st.session_state.pop("resultado_ejecucion", None)
        st.session_state.pop("decision_accion", None)
        st.session_state.pop("decision_nombre", None)

    preview = st.session_state.get("preview")
    if preview is not None:
        _mostrar_vista_previa_y_confirmar(preview)


if __name__ == "__main__":
    main()
