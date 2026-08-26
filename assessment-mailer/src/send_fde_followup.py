"""One-off follow-up: sends the Forward Deployed Engineer assessment PDF to
the specific candidates who already received the FDE assessment email
before that PDF existed (config.FDE_ASSESSMENT_PDF was added after those
emails went out). Not part of the recurring automation - has its own
workflow_dispatch-only GitHub Actions workflow (send-fde-followup.yml), run
manually, once.

Idempotent: records each sent follow-up's Message-ID in its own
FDEFollowUpsSent sheet tab (separate from the main AssessmentsSent tab, so
this never interferes with the regular scheduled run) and skips anyone
already in it, so re-running this script is always safe.
"""
import datetime

import gspread
from google.oauth2.service_account import Credentials

import config
import candidate_name
import gmail_reader
import mailer
import resume_text
import role_classifier

FOLLOWUP_RECIPIENTS = {
    "jaiminbhaisojitra@gmail.com",
    "omkarjagtap018@gmail.com",
    "milankoradiya.work@gmail.com",
    "aaratigaikwad0423@gmail.com",
    "avin3215@gmail.com",
    "rishabh.kapoor.ug22@gmail.com",
    "kathantrivedi12@gmail.com",
}

FOLLOWUP_SHEET_TITLE = "FDEFollowUpsSent"
FOLLOWUP_SHEET_HEADER = ["Message-ID", "Candidate Email", "Candidate Name", "Sent Date"]


def build_credentials():
    return Credentials.from_service_account_info(
        config.SERVICE_ACCOUNT_INFO, scopes=config.GOOGLE_SCOPES
    )


def _open_followup_worksheet(credentials):
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
    try:
        worksheet = spreadsheet.worksheet(FOLLOWUP_SHEET_TITLE)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=FOLLOWUP_SHEET_TITLE, rows=100, cols=len(FOLLOWUP_SHEET_HEADER)
        )
        worksheet.insert_row(FOLLOWUP_SHEET_HEADER, index=1)
        return worksheet

    first_row = worksheet.row_values(1)
    if first_row != FOLLOWUP_SHEET_HEADER:
        worksheet.insert_row(FOLLOWUP_SHEET_HEADER, index=1)
    return worksheet


def main():
    credentials = build_credentials()
    worksheet = _open_followup_worksheet(credentials)
    already_sent = set(worksheet.col_values(1)[1:])  # skip header row

    print(f"Scanning inbox(es) for {len(FOLLOWUP_RECIPIENTS)} target candidate(s)...", flush=True)
    # known_message_ids=set() so this re-fetches every matching application
    # since SINCE_DATE regardless of whether the main automation already
    # processed it - we need the original email's own content (subject,
    # references, resume) to build a properly threaded follow-up, not just
    # its Message-ID.
    candidates = gmail_reader.fetch_candidate_emails(known_message_ids=set())

    matched = [c for c in candidates if c["from_email"].lower() in FOLLOWUP_RECIPIENTS]
    print(f"Found {len(matched)} matching original application email(s) in inbox(es).", flush=True)

    sent = 0
    for candidate in matched:
        message_id = candidate["message_id"]
        from_email = candidate["from_email"]

        if message_id in already_sent:
            print(f"  - {from_email} already sent this follow-up, skipping", flush=True)
            continue

        role = role_classifier.classify(candidate["subject"])
        if role != role_classifier.FDE:
            print(
                f"  ! {from_email} is in the target list but subject {candidate['subject']!r} "
                f"did not classify as Forward Deployed Engineer (got {role!r}) - skipping to be safe",
                flush=True,
            )
            continue

        text = resume_text.extract_text(candidate["resume_filename"], candidate["resume_bytes"])
        name = candidate_name.resolve(candidate["display_name"], from_email, text)

        mailer.send_followup_email(
            from_email, name,
            original_message_id=message_id,
            original_references=candidate["references"],
            original_subject=candidate["subject"],
            send_address=candidate["send_address"],
            send_app_password=candidate["send_app_password"],
            pdf_path=config.FDE_ASSESSMENT_PDF,
        )

        worksheet.append_rows(
            [[message_id, from_email, name, datetime.date.today().isoformat()]],
            value_input_option="RAW",
        )
        sent += 1
        print(f"  + sent follow-up PDF to {from_email} ({name})", flush=True)

    missing = FOLLOWUP_RECIPIENTS - {c["from_email"].lower() for c in matched}
    if missing:
        print(f"Not found in inbox scan (outside SINCE_DATE, or no resume attached): {sorted(missing)}", flush=True)

    print(f"Done. Sent {sent} follow-up(s).", flush=True)


if __name__ == "__main__":
    main()
