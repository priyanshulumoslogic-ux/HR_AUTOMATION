import json
import os

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
DRIVE_FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"])

IMAP_HOST = "imap.gmail.com"
MAILBOX = "INBOX"

# Fixed forever - never roll this forward. Dedup happens against the sheet,
# so re-scanning the full range each run is cheap and avoids boundary misses.
SINCE_DATE = "01-Jan-2026"

# Non-redundant substrings covering apply/applying/application/applicant variants.
# IMAP SUBJECT search is already case-insensitive substring matching.
SUBJECT_KEYWORDS = ["apply", "application", "applicant"]

SHEET_HEADER = ["Applicant Email", "Applied Date", "Phone", "Resume Link", "Message-ID"]
MESSAGE_ID_COLUMN = len(SHEET_HEADER)  # 1-indexed, last column

RESUME_EXTENSIONS = (".pdf", ".docx")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
