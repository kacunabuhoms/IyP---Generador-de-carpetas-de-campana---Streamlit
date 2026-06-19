import streamlit as st


def get_drive_root_id(cliente: str) -> str | None:
    return st.secrets.get("drive_roots", {}).get(cliente)


def get_campaigns_api_url() -> str:
    return st.secrets["campaigns_api_url"]


def get_default_subfolders() -> list[str]:
    return list(st.secrets["default_subfolders"])


def get_app_password() -> str:
    return st.secrets["app_password"]
