from streamlit.testing.v1 import AppTest


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
