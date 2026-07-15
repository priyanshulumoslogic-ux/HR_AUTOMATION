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

# Real application emails in this inbox are candidates emailing directly with
# a resume attached, always phrased as "apply for ..." or "application for ...".
# Bare "apply"/"application" alone matched far too much unrelated mail
# (job-alert digests, newsletters), so we require the "for" phrase.
# IMAP SUBJECT search is already case-insensitive substring matching.
SUBJECT_KEYWORDS = ["apply for", "application for"]

SHEET_HEADER = ["Applicant Email", "Applied Date", "Role", "Phone", "Resume Link"]

# Message-IDs (the dedup key) live on a separate, second tab in the same
# spreadsheet rather than as a visible column on the main sheet.
DEDUP_SHEET_TITLE = "MessageIDs"
DEDUP_SHEET_HEADER = ["Message-ID"]

RESUME_EXTENSIONS = (".pdf", ".docx")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
