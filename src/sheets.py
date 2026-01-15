import gspread
from google.oauth2.service_account import Credentials
import os, json, base64


def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    key_b64 = os.environ["GOOGLE_SERVICE_ACCOUNT_B64"]
    creds_dict = json.loads(base64.b64decode(key_b64))
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(os.getenv("SPREADSHEET_ID")).worksheet(os.getenv("SHEET_NAME", "Sheet1"))


def get_existing_rows(sheet):
    rows = sheet.get_all_records()
    return {str(row["id"]): idx + 2 for idx, row in enumerate(rows)}
