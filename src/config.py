import json
import os

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
DRIVE_FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"])

IMAP_HOST = "imap.gmail.com"
# Without this, a stalled connection (network blip, Gmail throttling) hangs
# the blocking IMAP call forever instead of raising.
IMAP_TIMEOUT = 60
MAILBOX = "INBOX"

# Fixed forever - never roll this forward. Dedup happens against the sheet,
# so re-scanning the full range each run is cheap and avoids boundary misses.
SINCE_DATE = "01-Jan-2026"

# Subject phrases that qualify an email for consideration. The resume-
# attachment requirement (see gmail_client.py) is what actually distinguishes
# a genuine candidate email from an outside company/newsletter that happens
# to mention "intern"/"internship"/"job opportunity" - it applies to every
# keyword here, not just the "apply for"/"application for" ones.
# "intern" alone also matches "internship" as a substring, no need to list both.
# IMAP SUBJECT search is already case-insensitive substring matching.
SUBJECT_KEYWORDS = [
    "apply for", "application for", "applying for", "applied for",
    "intern", "job opportunity",
]

# Role extraction only knows how to strip a leading phrase like "apply for"/
# "applying for" and use whatever follows as the role. Subjects matched via
# the other keywords above (e.g. "AIML intern", "Regarding qa opportunity")
# don't follow that pattern - the role comes before the keyword, not after -
# so role_parser falls back to using the whole subject when none of these match.
ROLE_PREFIX_KEYWORDS = ["apply for", "application for", "applying for", "applied for"]

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
