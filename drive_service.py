import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

_SCOPES = ["https://www.googleapis.com/auth/drive"]
_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


def build_client():
    credentials = service_account.Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=_SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def _escape_name(name: str) -> str:
    return name.replace("\\", "\\\\").replace("'", "\\'")


def find_child_folder(drive, parent_id: str, name: str) -> str | None:
    query = (
        f"name = '{_escape_name(name)}' and "
        f"'{parent_id}' in parents and "
        f"mimeType = '{_FOLDER_MIME_TYPE}' and "
        "trashed = false"
    )
    response = (
        drive.files()
        .list(q=query, fields="files(id, name)", spaces="drive")
        .execute()
    )
    files = response.get("files", [])
    if not files:
        return None
    return files[0]["id"]


def create_folder(drive, parent_id: str, name: str) -> str:
    metadata = {"name": name, "mimeType": _FOLDER_MIME_TYPE, "parents": [parent_id]}
    created = drive.files().create(body=metadata, fields="id").execute()
    return created["id"]


def get_folder_link(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"
