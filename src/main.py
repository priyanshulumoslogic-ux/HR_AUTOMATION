from google.oauth2.service_account import Credentials

import config
import drive_client
import gmail_client
import resume_parser
import sheets_client


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
        phone,
        resume_link,
        application["message_id"],
    ]


def main():
    credentials = build_credentials()

    worksheet, known_message_ids = sheets_client.get_known_message_ids(credentials)
    print(f"Loaded {len(known_message_ids)} previously recorded application(s).")

    applications = gmail_client.fetch_matching_applications(known_message_ids)
    print(f"Found {len(applications)} new matching email(s).")

    rows = []
    seen_this_run = set()
    for application in applications:
        message_id = application["message_id"]
        if message_id in seen_this_run:
            continue
        seen_this_run.add(message_id)

        row = process_application(credentials, application)
        rows.append(row)
        print(f"  + {row[0]} | applied {row[1]} | phone {row[2]}")

    sheets_client.append_rows(worksheet, rows)
    print(f"Done. Appended {len(rows)} new row(s) to the sheet.")


if __name__ == "__main__":
    main()
