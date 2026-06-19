from streamlit.testing.v1 import AppTest

import campaigns_service


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
