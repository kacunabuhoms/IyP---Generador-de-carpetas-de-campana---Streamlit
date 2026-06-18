from unittest.mock import MagicMock, patch

import drive_service


def test_find_child_folder_returns_id_when_found():
    drive = MagicMock()
    drive.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": "folder123", "name": "FDA 2026"}]
    }
    result = drive_service.find_child_folder(drive, "root1", "FDA 2026")
    assert result == "folder123"


def test_find_child_folder_returns_none_when_not_found():
    drive = MagicMock()
    drive.files.return_value.list.return_value.execute.return_value = {"files": []}
    result = drive_service.find_child_folder(drive, "root1", "FDA 2026")
    assert result is None


def test_find_child_folder_escapes_single_quotes_in_query():
    drive = MagicMock()
    drive.files.return_value.list.return_value.execute.return_value = {"files": []}
    drive_service.find_child_folder(drive, "root1", "O'Brien")
    called_query = drive.files.return_value.list.call_args.kwargs["q"]
    assert "O\\'Brien" in called_query


def test_create_folder_returns_new_id():
    drive = MagicMock()
    drive.files.return_value.create.return_value.execute.return_value = {"id": "new123"}
    result = drive_service.create_folder(drive, "parent1", "Fotos")
    assert result == "new123"
    drive.files.return_value.create.assert_called_once_with(
        body={
            "name": "Fotos",
            "mimeType": drive_service._FOLDER_MIME_TYPE,
            "parents": ["parent1"],
        },
        fields="id",
    )


def test_get_folder_link_builds_drive_url():
    assert drive_service.get_folder_link("abc123") == "https://drive.google.com/drive/folders/abc123"


def test_build_client_uses_service_account_credentials():
    fake_secrets = {"gcp_service_account": {"type": "service_account", "project_id": "p1"}}
    with patch.object(drive_service.st, "secrets", fake_secrets), \
         patch.object(drive_service.service_account.Credentials, "from_service_account_info") as mock_creds, \
         patch.object(drive_service, "build") as mock_build:
        mock_creds.return_value = "fake-creds"
        mock_build.return_value = "fake-drive-client"
        result = drive_service.build_client()
        mock_creds.assert_called_once_with(
            fake_secrets["gcp_service_account"], scopes=drive_service._SCOPES
        )
        mock_build.assert_called_once_with("drive", "v3", credentials="fake-creds")
        assert result == "fake-drive-client"
