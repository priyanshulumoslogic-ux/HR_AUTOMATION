import json
import os

# --- Reading candidate applications (same inbox the Indeed scraper reads) ---
READ_GMAIL_ADDRESS = os.environ["READ_GMAIL_ADDRESS"]
READ_GMAIL_APP_PASSWORD = os.environ["READ_GMAIL_APP_PASSWORD"]

# --- Sending assessment emails (HR mailbox) ---
SEND_GMAIL_ADDRESS = os.environ["SEND_GMAIL_ADDRESS"]
SEND_GMAIL_APP_PASSWORD = os.environ["SEND_GMAIL_APP_PASSWORD"]

# Every application inbox this reads from, paired with the address the reply
# should be sent from. The original mailbox reads from one address
# (READ_GMAIL_ADDRESS) and replies from a separate HR sender
# (SEND_GMAIL_ADDRESS). GMAIL_ADDRESS_2 is a second, self-contained mailbox
# that both receives applications and sends its own replies from itself, so
# read and send addresses/passwords are the same for it. Optional - only
# added once its secrets exist, so the existing single-mailbox setup keeps
# working untouched if it's never set.
MAILBOXES = [
    {
        "read_address": READ_GMAIL_ADDRESS,
        "read_app_password": READ_GMAIL_APP_PASSWORD,
        "send_address": SEND_GMAIL_ADDRESS,
        "send_app_password": SEND_GMAIL_APP_PASSWORD,
    },
]
_address_2 = os.environ.get("GMAIL_ADDRESS_2")
if _address_2:
    _app_password_2 = os.environ["GMAIL_APP_PASSWORD_2"]
    MAILBOXES.append({
        "read_address": _address_2,
        "read_app_password": _app_password_2,
        "send_address": _address_2,
        "send_app_password": _app_password_2,
    })

# --- Dedup tracking sheet (same spreadsheet the Indeed scraper writes to) ---
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"])

IMAP_HOST = "imap.gmail.com"
# Without this, a stalled connection (network blip, Gmail throttling) hangs
# the blocking IMAP call forever instead of raising - which then blocks every
# later scheduled run too, since this workflow only allows one run at a time.
IMAP_TIMEOUT = 60
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
MAILBOX = "INBOX"

# Unlike the Indeed scraper (which only ever adds spreadsheet rows), this
# script sends real emails to real candidates - so, deliberately, it does
# NOT mirror the Indeed scraper's "fixed forever, since Jan 1" cutoff. That
# pattern is safe for a script whose worst-case re-run mistake is a
# duplicate sheet row, but not for one whose worst-case mistake is mass-
# emailing a mailbox's entire history the first time it runs (which is
# exactly what happened before this cutoff existed). Bump this forward
# periodically if needed, but never back past a date you're comfortable
# emailing every unprocessed matching applicant since. Dedup against the
# AssessmentsSent sheet is what actually prevents repeat sends day to day;
# this date is purely a blast-radius bound if that sheet is ever reset.
SINCE_DATE = "24-Jul-2026"

# Same broad set the Indeed scraper searches on - this is what qualifies an
# email as "an application" at all. Role classification (QA vs Full Stack)
# happens afterwards, on top of this.
SUBJECT_KEYWORDS = [
    "apply for", "application for", "applying for", "applied for",
    "intern", "job opportunity",
    # Bare "application" catches subjects that state the word without "for"
    # right after it, e.g. "<Role> Application - <Name>" (missed a real
    # Forward Deployed Engineer applicant before this was added). The
    # required resume attachment (see gmail_reader.py) is what keeps this
    # from over-matching newsletters that merely mention "application".
    "application",
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
PRODUCT_ENGINEER_ASSESSMENT_PDF = os.path.join(ASSETS_DIR, "Product_Engineer_Assessment.pdf")
FDE_ASSESSMENT_PDF = os.path.join(ASSETS_DIR, "Forward_Deployed_Engineer_Assessment.pdf")

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
