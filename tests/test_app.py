import pandas as pd
from streamlit.testing.v1 import AppTest

import campaigns_service
import drive_service
import folder_planner


_CAMPANAS_DF = pd.DataFrame(
    {
        "campaign_id": [1, 2, 3],
        "campana": ["Campana A", "Campana B", "Campana C"],
        "cliente": ["FDA", "FDA", "DQ"],
        "fecha_inicio": [None, None, None],
        "fecha_fin": [None, None, None],
    }
)


def _app_logueada(monkeypatch) -> AppTest:
    monkeypatch.setattr(campaigns_service, "get_campaigns", lambda: _CAMPANAS_DF)
    monkeypatch.setattr(drive_service, "build_client", lambda: "drive-client-stub")
    monkeypatch.setattr(folder_planner.drive_service, "find_child_folder", lambda drive, parent_id, name: None)

    at = AppTest.from_file("app.py")
    at.secrets["app_password"] = "clave-correcta"
    at.secrets["drive_roots"] = {"FDA": "root-fda", "DQ": "root-dq"}
    at.secrets["default_subfolders"] = ["Fotos", "Totales"]
    at.run(timeout=10)
    at.text_input[0].set_value("clave-correcta").run(timeout=10)
    at.button[0].click().run(timeout=10)
    return at


def test_campaign_load_failure_shows_technical_details_in_expander(monkeypatch):
    def fake_get_campaigns():
        raise RuntimeError("boom")

    monkeypatch.setattr(campaigns_service, "get_campaigns", fake_get_campaigns)

    at = AppTest.from_file("app.py")
    at.secrets["app_password"] = "clave-correcta"
    at.run(timeout=10)
    at.text_input[0].set_value("clave-correcta").run(timeout=10)
    at.button[0].click().run(timeout=10)

    assert len(at.error) == 1
    assert at.error[0].value == "No se pudo obtener las campañas."
    assert len(at.exception) == 1
    assert "boom" in at.exception[0].value


def test_password_gate_blocks_without_correct_password():
    at = AppTest.from_file("app.py")
    at.secrets["app_password"] = "clave-correcta"
    at.run()

    assert len(at.error) == 0
    assert len(at.text_input) == 1
    assert "campanas_df" not in at.session_state


def test_password_gate_shows_error_with_wrong_password():
    at = AppTest.from_file("app.py")
    at.secrets["app_password"] = "clave-correcta"
    at.run()
    at.text_input[0].set_value("incorrecta").run()
    at.button[0].click().run()

    assert len(at.error) == 1
    assert "campanas_df" not in at.session_state


def test_selecting_cliente_shows_existe_en_claw_buttons(monkeypatch):
    at = _app_logueada(monkeypatch)

    assert len(at.selectbox) == 1
    labels = [b.label for b in at.button]
    assert "Sí" in labels
    assert "No" in labels


def test_clicking_si_shows_campana_dropdown(monkeypatch):
    at = _app_logueada(monkeypatch)
    at.selectbox[0].select("FDA").run(timeout=10)
    at.button(key="existe_en_claw_si").click().run(timeout=10)

    assert len(at.selectbox) == 2
    assert at.selectbox[1].label == "Campaña"
    assert at.selectbox[1].options == ["Campana A", "Campana B"]


def test_clicking_no_shows_nombre_exacto_textbox(monkeypatch):
    at = _app_logueada(monkeypatch)
    at.selectbox[0].select("FDA").run(timeout=10)
    at.button(key="existe_en_claw_no").click().run(timeout=10)

    assert at.text_input[0].label == "Nombre EXACTO que tendrá la campaña en CLAW"


def test_existe_en_claw_buttons_remain_visible_after_choosing(monkeypatch):
    at = _app_logueada(monkeypatch)
    at.selectbox[0].select("FDA").run(timeout=10)
    at.button(key="existe_en_claw_si").click().run(timeout=10)

    labels = [b.label for b in at.button]
    assert "Sí" in labels
    assert "No" in labels
    assert len(at.selectbox) == 2


def test_changing_cliente_resets_existe_en_claw_choice(monkeypatch):
    at = _app_logueada(monkeypatch)
    at.selectbox[0].select("FDA").run(timeout=10)
    at.button(key="existe_en_claw_si").click().run(timeout=10)
    assert len(at.selectbox) == 2

    at.selectbox[0].select("DQ").run(timeout=10)

    assert len(at.selectbox) == 1
    labels = [b.label for b in at.button]
    assert "Sí" in labels
    assert "No" in labels


def test_generar_with_existe_si_builds_preview_directly(monkeypatch):
    at = _app_logueada(monkeypatch)
    at.selectbox[0].select("FDA").run(timeout=10)
    at.button(key="existe_en_claw_si").click().run(timeout=10)
    at.selectbox[1].select("Campana A").run(timeout=10)
    at.button(key="boton_generar").click().run(timeout=10)

    assert len(at.error) == 0
    assert len(at.code) == 1


def test_generar_with_existe_no_opens_confirmation_dialog_with_name(monkeypatch):
    at = _app_logueada(monkeypatch)
    at.selectbox[0].select("FDA").run(timeout=10)
    at.button(key="existe_en_claw_no").click().run(timeout=10)
    at.text_input[0].set_value("Campana Nueva XYZ").run(timeout=10)
    at.button(key="boton_generar").click().run(timeout=10)

    textos = [m.value for m in at.markdown]
    assert any("Campana Nueva XYZ" in t for t in textos)
    assert len(at.code) == 0


def test_generar_with_no_and_empty_name_shows_error_without_opening_dialog(monkeypatch):
    at = _app_logueada(monkeypatch)
    at.selectbox[0].select("FDA").run(timeout=10)
    at.button(key="existe_en_claw_no").click().run(timeout=10)
    at.button(key="boton_generar").click().run(timeout=10)

    assert len(at.error) == 1
    assert len(at.code) == 0
