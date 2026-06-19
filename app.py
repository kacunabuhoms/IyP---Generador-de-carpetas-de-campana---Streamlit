from datetime import date

import streamlit as st

import campaign_data
import campaigns_service
import config
import drive_service
import folder_planner

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


def _cargar_campanas() -> bool:
    try:
        st.session_state["campanas_df"] = campaigns_service.get_campaigns()
        return True
    except Exception as e:
        st.error("No se pudo obtener las campañas.")
        with st.expander("Detalles técnicos"):
            st.exception(e)
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

    subcarpetas = config.get_default_subfolders() + st.session_state.get("carpetas_extra", [])

    reutilizando_campana = accion == "reusar" and preview.campana.existe
    campana_id_para_check = preview.campana.folder_id if reutilizando_campana else None
    drive_lectura = drive_service.build_client()
    subcarpetas_preview = folder_planner.build_subfolder_preview(
        drive_lectura, campana_id_para_check, subcarpetas
    )
    st.code(
        folder_planner.render_tree(preview.anio, nombre_final, reutilizando_campana, subcarpetas_preview)
    )

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


def _generar_preview(cliente_clave: str, nombre_campana: str, anio: int, carpetas_extra: list[str]) -> None:
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


@st.dialog("Confirmar nombre en Claw")
def _abrir_confirmacion_nombre(cliente_clave: str, nombre_campana: str, anio: int, carpetas_extra: list[str]) -> None:
    st.write(f"¿Así se llamará la campaña **'{nombre_campana}'** en Claw?")
    col_confirmar, col_cancelar = st.columns(2)
    if col_confirmar.button("Confirmar", key="confirmar_nombre_claw"):
        _generar_preview(cliente_clave, nombre_campana, anio, carpetas_extra)
        st.rerun()
    if col_cancelar.button("Cancelar", key="cancelar_nombre_claw"):
        st.rerun()


def main() -> None:
    st.title("Generador de carpetas de campaña")

    if not _gate_de_contrasena():
        return

    if "campanas_df" not in st.session_state:
        if not _cargar_campanas():
            return

    if st.button("🔄 Refrescar campañas"):
        if _cargar_campanas():
            st.session_state.pop("preview", None)
            st.session_state.pop("resultado_ejecucion", None)

    df = st.session_state["campanas_df"]

    clientes = campaign_data.unique_clients(df)
    cliente_clave = st.selectbox("Cliente", clientes)

    if st.session_state.get("cliente_anterior") != cliente_clave:
        st.session_state["cliente_anterior"] = cliente_clave
        st.session_state["existe_en_claw"] = None
        st.session_state.pop("preview", None)
        st.session_state.pop("resultado_ejecucion", None)

    existe_en_claw = st.session_state.get("existe_en_claw")

    if existe_en_claw is None:
        st.write("¿La campaña ya existe en Claw?")
        col_si, col_no = st.columns(2)
        if col_si.button("Sí", key="existe_en_claw_si"):
            st.session_state["existe_en_claw"] = True
            st.rerun()
        if col_no.button("No", key="existe_en_claw_no"):
            st.session_state["existe_en_claw"] = False
            st.rerun()
        return

    if existe_en_claw:
        campanas_cliente = campaign_data.campaigns_for_client(df, cliente_clave)
        nombre_campana = st.selectbox("Campaña", campanas_cliente["campana"].tolist())
    else:
        nombre_campana = st.text_input("Nombre EXACTO que tendrá la campaña en CLAW")

    anio_default = folder_planner.compute_default_year(date.today())
    anio = st.number_input("Año", min_value=2000, max_value=2100, value=anio_default, step=1)

    carpetas_extra_texto = st.text_input("Carpetas extra (separadas por coma, opcional)")
    carpetas_extra = _parsear_carpetas_extra(carpetas_extra_texto)

    if st.button("Generar", key="boton_generar"):
        if existe_en_claw:
            _generar_preview(cliente_clave, nombre_campana, int(anio), carpetas_extra)
        elif not nombre_campana.strip():
            st.error("Escribe el nombre de la campaña.")
        else:
            _abrir_confirmacion_nombre(cliente_clave, nombre_campana, int(anio), carpetas_extra)

    preview = st.session_state.get("preview")
    if preview is not None:
        _mostrar_vista_previa_y_confirmar(preview)


if __name__ == "__main__":
    main()
