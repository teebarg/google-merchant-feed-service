import base64
import json
import os
from unittest.mock import MagicMock, patch

from src.sheets import get_existing_rows, get_sheet


class TestGetSheet:
    """Tests for get_sheet function."""

    @patch("src.sheets.os.getenv")
    @patch("src.sheets.gspread.authorize")
    @patch("src.sheets.Credentials.from_service_account_info")
    def test_get_sheet_success(
        self, mock_creds_from_info, mock_authorize, mock_getenv
    ):
        """Test successful sheet retrieval."""
        # Mock service account JSON
        service_account_json = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
        }
        encoded_json = base64.b64encode(json.dumps(service_account_json).encode()).decode()

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "GOOGLE_SERVICE_ACCOUNT_B64": encoded_json,
            "SPREADSHEET_ID": "test-spreadsheet-id",
            "SHEET_NAME": "Sheet1",
        }.get(key, default)

        # Mock credentials and client
        mock_creds = MagicMock()
        mock_creds_from_info.return_value = mock_creds
        mock_client = MagicMock()
        mock_authorize.return_value = mock_client
        mock_worksheet = MagicMock()
        mock_client.open_by_key.return_value.worksheet.return_value = mock_worksheet

        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_B64": encoded_json}):
            result = get_sheet()

        assert result == mock_worksheet
        mock_creds_from_info.assert_called_once()
        mock_authorize.assert_called_once_with(mock_creds)
        mock_client.open_by_key.assert_called_once_with("test-spreadsheet-id")
        mock_client.open_by_key.return_value.worksheet.assert_called_once_with("Sheet1")

    @patch("src.sheets.os.getenv")
    @patch("src.sheets.gspread.authorize")
    @patch("src.sheets.Credentials.from_service_account_info")
    def test_get_sheet_default_sheet_name(
        self, mock_creds_from_info, mock_authorize, mock_getenv
    ):
        """Test that default sheet name is used when not provided."""
        service_account_json = {"type": "service_account"}
        encoded_json = base64.b64encode(json.dumps(service_account_json).encode()).decode()

        mock_getenv.side_effect = lambda key, default=None: {
            "GOOGLE_SERVICE_ACCOUNT_B64": encoded_json,
            "SPREADSHEET_ID": "test-spreadsheet-id",
        }.get(key, default)

        mock_creds = MagicMock()
        mock_creds_from_info.return_value = mock_creds
        mock_client = MagicMock()
        mock_authorize.return_value = mock_client
        mock_worksheet = MagicMock()
        mock_client.open_by_key.return_value.worksheet.return_value = mock_worksheet

        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_B64": encoded_json}):
            result = get_sheet()

        mock_client.open_by_key.return_value.worksheet.assert_called_once_with("Sheet1")


class TestGetExistingRows:
    """Tests for get_existing_rows function."""

    def test_get_existing_rows_with_data(self):
        """Test retrieving existing rows from sheet."""
        mock_sheet = MagicMock()
        mock_sheet.get_all_records.return_value = [
            {"id": "SKU-001", "title": "Product 1"},
            {"id": "SKU-002", "title": "Product 2"},
            {"id": "SKU-003", "title": "Product 3"},
        ]

        result = get_existing_rows(mock_sheet)

        assert result == {
            "SKU-001": 2,  # Row 2 (header is row 1, so first data row is 2)
            "SKU-002": 3,
            "SKU-003": 4,
        }
        mock_sheet.get_all_records.assert_called_once()

    def test_get_existing_rows_empty_sheet(self):
        """Test retrieving rows from empty sheet."""
        mock_sheet = MagicMock()
        mock_sheet.get_all_records.return_value = []

        result = get_existing_rows(mock_sheet)

        assert result == {}

    def test_get_existing_rows_with_numeric_ids(self):
        """Test that numeric IDs are converted to strings."""
        mock_sheet = MagicMock()
        mock_sheet.get_all_records.return_value = [
            {"id": 123, "title": "Product 1"},
            {"id": "SKU-002", "title": "Product 2"},
        ]

        result = get_existing_rows(mock_sheet)

        assert "123" in result
        assert result["123"] == 2
        assert result["SKU-002"] == 3
