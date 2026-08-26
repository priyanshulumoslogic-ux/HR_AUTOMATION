import datetime
import signal

from google.oauth2.service_account import Credentials

import candidate_name
import config
import gmail_reader
import mailer
import resume_text
import role_classifier
import sheets_client

PROCESS_TIMEOUT_SECONDS = 90

_ROLE_LABEL = {
    role_classifier.QA: "QA Intern",
    role_classifier.FULLSTACK: "Full Stack Intern",
    role_classifier.GRAPHIC: "Graphic Designer",
    role_classifier.RECRUITER: "Recruiter Intern",
    role_classifier.AI_NATIVE: "AI Native Intern",
    role_classifier.MOBILE: "Mobile Application Intern",
    role_classifier.FDE: "Forward Deployed Engineer",
    role_classifier.PRODUCT_ENGINEER: "Product Engineer",
}


class ProcessingTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise ProcessingTimeout()


def build_credentials():
    return Credentials.from_service_account_info(
        config.SERVICE_ACCOUNT_INFO, scopes=config.GOOGLE_SCOPES
    )


def process_candidate(candidate):
    role = role_classifier.classify(candidate["subject"])
    if role is None:
        return None, "not QA or Full Stack (or ambiguous) - skipped"

    text = resume_text.extract_text(candidate["resume_filename"], candidate["resume_bytes"])
    name = candidate_name.resolve(candidate["display_name"], candidate["from_email"], text)

    mailer.send_assessment_email(
        candidate["from_email"], name, role,
        original_message_id=candidate["message_id"],
        original_references=candidate["references"],
        original_subject=candidate["subject"],
        send_address=candidate["send_address"],
        send_app_password=candidate["send_app_password"],
    )

    row = [
        candidate["message_id"],
        candidate["from_email"],
        name,
        _ROLE_LABEL[role],
        datetime.date.today().isoformat(),
    ]
    return row, None


def main():
    credentials = build_credentials()

    sent_worksheet = sheets_client.open_sent_worksheet(credentials)
    known_message_ids = sheets_client.get_known_message_ids(sent_worksheet)
    print(f"Loaded {len(known_message_ids)} previously sent assessment(s).", flush=True)

    candidates = gmail_reader.fetch_candidate_emails(known_message_ids)
    print(f"Found {len(candidates)} new candidate email(s).", flush=True)

    seen_this_run = set()
    total_sent = 0

    for i, candidate in enumerate(candidates, start=1):
        message_id = candidate["message_id"]
        if message_id in seen_this_run:
            continue
        seen_this_run.add(message_id)

        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(PROCESS_TIMEOUT_SECONDS)
        try:
            row, skip_reason = process_candidate(candidate)
        except ProcessingTimeout:
            print(
                f"  [{i}/{len(candidates)}] ! TIMED OUT after {PROCESS_TIMEOUT_SECONDS}s on "
                f"{candidate['from_email']} - skipping, will retry next run",
                flush=True,
            )
            continue
        except Exception as exc:
            print(f"  [{i}/{len(candidates)}] ! FAILED for {candidate['from_email']}: {exc}", flush=True)
            continue
        finally:
            signal.alarm(0)

        if skip_reason:
            print(f"  [{i}/{len(candidates)}] - {candidate['from_email']} | {candidate['subject']!r} | {skip_reason}", flush=True)
            continue

        # Recorded immediately after each send (not batched): the email
        # itself can't be un-sent, so the dedup row must land before moving
        # on to the next candidate - otherwise a crash mid-run could send
        # the same candidate a duplicate assessment on the next run.
        sheets_client.append_rows(sent_worksheet, [row])
        total_sent += 1
        print(f"  [{i}/{len(candidates)}] + sent {row[3]} assessment to {row[1]} ({row[2]})", flush=True)

    print(f"Done. Sent {total_sent} new assessment email(s).", flush=True)


if __name__ == "__main__":
    main()
