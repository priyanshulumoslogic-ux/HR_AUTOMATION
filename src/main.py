import signal

from google.oauth2.service_account import Credentials

import config
import drive_client
import gmail_client
import resume_parser
import sheets_client

PROCESS_TIMEOUT_SECONDS = 90


class ProcessingTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise ProcessingTimeout()


def build_credentials():
    return Credentials.from_service_account_info(
        config.SERVICE_ACCOUNT_INFO, scopes=config.GOOGLE_SCOPES
    )


def process_application(credentials, application):
    resume_filename = application["resume_filename"]
    resume_bytes = application["resume_bytes"]

    phone = resume_parser.NOT_CAPTURED
    resume_link = ""

    if resume_filename and resume_bytes:
        text = resume_parser.extract_text(resume_filename, resume_bytes)
        phone = resume_parser.extract_phone(text)
        resume_link = drive_client.upload_and_share(
            credentials, config.DRIVE_FOLDER_ID, resume_filename, resume_bytes
        )

    return [
        application["from_email"],
        application["applied_date"],
        application["role"],
        phone,
        resume_link,
    ]


BATCH_SIZE = 10


def main():
    credentials = build_credentials()

    main_worksheet, dedup_worksheet = sheets_client.open_worksheets(credentials)
    known_message_ids = sheets_client.get_known_message_ids(dedup_worksheet)
    print(f"Loaded {len(known_message_ids)} previously recorded application(s).", flush=True)

    applications = gmail_client.fetch_matching_applications(known_message_ids)
    print(f"Found {len(applications)} new matching email(s).", flush=True)

    pending_rows = []
    pending_message_ids = []
    seen_this_run = set()
    total_appended = 0

    for i, application in enumerate(applications, start=1):
        message_id = application["message_id"]
        if message_id in seen_this_run:
            continue
        seen_this_run.add(message_id)

        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(PROCESS_TIMEOUT_SECONDS)
        try:
            row = process_application(credentials, application)
        except ProcessingTimeout:
            print(
                f"  [{i}/{len(applications)}] ! TIMED OUT after {PROCESS_TIMEOUT_SECONDS}s on "
                f"{application['from_email']} - skipping, will retry next run",
                flush=True,
            )
            continue
        finally:
            signal.alarm(0)

        pending_rows.append(row)
        pending_message_ids.append([message_id])
        print(f"  [{i}/{len(applications)}] + {row[0]} | applied {row[1]} | role {row[2]} | phone {row[3]}", flush=True)

        if len(pending_rows) >= BATCH_SIZE:
            # Write the visible rows before the dedup keys: if something
            # fails between the two calls, worst case is a possible
            # duplicate row next run (visible, easy to spot and delete),
            # never a candidate silently missing from the sheet entirely.
            sheets_client.append_rows(main_worksheet, pending_rows)
            sheets_client.append_rows(dedup_worksheet, pending_message_ids)
            total_appended += len(pending_rows)
            print(f"  -- saved batch of {len(pending_rows)} to the sheet ({total_appended} so far)", flush=True)
            pending_rows = []
            pending_message_ids = []

    if pending_rows:
        sheets_client.append_rows(main_worksheet, pending_rows)
        sheets_client.append_rows(dedup_worksheet, pending_message_ids)
        total_appended += len(pending_rows)

    print(f"Done. Appended {total_appended} new row(s) to the sheet.", flush=True)


if __name__ == "__main__":
    main()
