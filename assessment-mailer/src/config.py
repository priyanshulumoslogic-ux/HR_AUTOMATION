import json
import os

# --- Reading candidate applications (same inbox the Indeed scraper reads) ---
READ_GMAIL_ADDRESS = os.environ["READ_GMAIL_ADDRESS"]
READ_GMAIL_APP_PASSWORD = os.environ["READ_GMAIL_APP_PASSWORD"]

# --- Sending assessment emails (HR mailbox) ---
SEND_GMAIL_ADDRESS = os.environ["SEND_GMAIL_ADDRESS"]
SEND_GMAIL_APP_PASSWORD = os.environ["SEND_GMAIL_APP_PASSWORD"]

# --- Dedup tracking sheet (same spreadsheet the Indeed scraper writes to) ---
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"])

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
MAILBOX = "INBOX"

# Fixed forever - never roll this forward. Dedup happens against the sheet,
# so re-scanning the full range each run is cheap and avoids boundary misses.
SINCE_DATE = "01-Jan-2026"

# Same broad set the Indeed scraper searches on - this is what qualifies an
# email as "an application" at all. Role classification (QA vs Full Stack)
# happens afterwards, on top of this.
SUBJECT_KEYWORDS = [
    "apply for", "application for", "applying for", "applied for",
    "intern", "job opportunity",
]

RESUME_EXTENSIONS = (".pdf", ".docx")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

# Message-IDs of candidates who already received an assessment email live on
# their own tab in the same spreadsheet the Indeed scraper uses, so re-runs
# never send a duplicate assessment.
SENT_SHEET_TITLE = "AssessmentsSent"
SENT_SHEET_HEADER = ["Message-ID", "Candidate Email", "Candidate Name", "Role", "Sent Date"]

# Same submission form is used for every role.
ASSESSMENT_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeuyGAmsgAzIuxaX1mgWC4XQByWjBv9zqmVXW7T5IOCCtYgiA/viewform"

# "Task details" doc for the AI Native roles - the instructions doc,
# separate from the submission form above.
AI_NATIVE_DOC_URL = "https://docs.google.com/document/d/1kZeAuI0jcc_v7S1j2qmzu6xeLDDAlccOjzR45tz6Ysg/edit?tab=t.0"

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
QA_ASSESSMENT_PDF = os.path.join(ASSETS_DIR, "QA_Intern_Technical_Assessment.pdf")
FULLSTACK_ASSESSMENT_PDF = os.path.join(ASSETS_DIR, "FullStack_Intern_Technical_Assessment.pdf")
GRAPHIC_ASSESSMENT_PDF = os.path.join(ASSETS_DIR, "Graphic_Designer_Assessment.pdf")
RECRUITER_ASSESSMENT_PDF = os.path.join(ASSETS_DIR, "Recruiter_Intern_Assessment_Task.pdf")

# Prepended to the top of every assessment email so candidates see the
# internship terms before the assessment itself.
TERMS_MESSAGE = """Before you apply, we'd like to inform you that this is a 3 to 6-month remote internship.

Please note that this internship is unpaid during the internship period. Based on your performance, consistency, and contribution throughout the internship, you may become eligible for a performance-based stipend.

If you're comfortable with these terms, we'd be happy to receive your application."""

SIGNATURE = """Best regards,
Kiara Dave
HR Team | Lumos Logic
kiara.dave@lumoslogic.com
www.lumoslogic.com
+91 63539 67527"""
