import os

import streamlit as st

_DRIVE_ROOT_ENV_VARS = {
    "FDA": "DRIVE_ROOT_FDA",
    "FAB": "DRIVE_ROOT_FAB",
    "DQ": "DRIVE_ROOT_DQ",
    "YZA": "DRIVE_ROOT_YZA",
}


def get_drive_root_id(cliente: str) -> str | None:
    env_var = _DRIVE_ROOT_ENV_VARS.get(cliente)
    if env_var is None:
        return None
    return os.environ.get(env_var)


def get_default_subfolders() -> list[str]:
    return list(st.secrets["default_subfolders"])


def get_app_password() -> str:
    return st.secrets["app_password"]
