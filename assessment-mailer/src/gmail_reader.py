import email
import hashlib
import imaplib
from email.header import decode_header, make_header
from email.utils import parseaddr

import config


def _build_search_criteria():
    subject_clause = f'(SUBJECT "{config.SUBJECT_KEYWORDS[-1]}")'
    for keyword in reversed(config.SUBJECT_KEYWORDS[:-1]):
        subject_clause = f'(OR (SUBJECT "{keyword}") {subject_clause})'
    return f'(SINCE "{config.SINCE_DATE}") {subject_clause}'


def _message_id_for(msg, raw_bytes):
    message_id = msg.get("Message-ID")
    if message_id:
        return message_id.strip()
    # Rare malformed email with no Message-ID header - derive a stable key
    # instead of skipping it outright.
    digest = hashlib.sha256(raw_bytes).hexdigest()[:32]
    return f"nomsgid:{digest}"


def _subject_for(msg):
    raw = msg.get("Subject", "")
    try:
        return str(make_header(decode_header(raw)))
    except (ValueError, LookupError):
        return raw


def _references_for(msg):
    return (msg.get("References") or "").strip()


def _from_for(msg):
    raw = msg.get("From", "")
    display_name, addr = parseaddr(raw)
    try:
        display_name = str(make_header(decode_header(display_name)))
    except (ValueError, LookupError):
        pass
    return display_name, addr


def _pick_resume_attachment(msg):
    candidates = []
    for part in msg.walk():
        filename = part.get_filename()
        if not filename:
            continue
        if not filename.lower().endswith(config.RESUME_EXTENSIONS):
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        candidates.append((filename, payload))

    if not candidates:
        return None, None

    for filename, payload in candidates:
        lowered = filename.lower()
        if "resume" in lowered or "cv" in lowered:
            return filename, payload

    return candidates[0]


def fetch_candidate_emails(known_message_ids):
    """Connects over IMAP to the inbox that receives applications, searches
    for application emails, and returns a list of dicts for messages not
    already present in known_message_ids. Each dict: message_id, references,
    subject, display_name, from_email, resume_filename, resume_bytes.
    message_id/references are threaded back into the outgoing reply's
    In-Reply-To/References headers so the assessment lands in the same
    Gmail thread as the candidate's original application instead of as a
    new, disconnected email. A resume attachment is required, same signal
    the Indeed scraper uses to tell a genuine application apart from a
    newsletter that merely mentions one of the subject keywords.
    """
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, timeout=config.IMAP_TIMEOUT)
    try:
        imap.login(config.READ_GMAIL_ADDRESS, config.READ_GMAIL_APP_PASSWORD)
        imap.select(config.MAILBOX, readonly=True)

        typ, data = imap.search(None, _build_search_criteria())
        if typ != "OK":
            raise RuntimeError(f"IMAP search failed: {typ} {data}")

        message_nums = data[0].split()
        print(f"IMAP search matched {len(message_nums)} email(s), fetching each one...", flush=True)

        results = []
        skipped_no_resume = 0
        skipped_known = 0
        for fetch_i, num in enumerate(message_nums, start=1):
            if fetch_i == 1 or fetch_i % 25 == 0 or fetch_i == len(message_nums):
                print(f"  fetching {fetch_i}/{len(message_nums)}...", flush=True)

            # Most matched messages here are ones already sent an assessment
            # on a past run. A full RFC822 fetch downloads the whole email
            # plus every attachment, so doing that just to throw the result
            # away wastes most of each run's time as the mailbox grows. Check
            # the Message-ID with a cheap header-only fetch first and skip
            # the full download when it's already known.
            typ, hdr_data = imap.fetch(num, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")
            if typ == "OK" and hdr_data and hdr_data[0]:
                probe_id = email.message_from_bytes(hdr_data[0][1]).get("Message-ID")
                if probe_id and probe_id.strip() in known_message_ids:
                    skipped_known += 1
                    continue

            typ, msg_data = imap.fetch(num, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue

            raw_bytes = msg_data[0][1]
            msg = email.message_from_bytes(raw_bytes)
            message_id = _message_id_for(msg, raw_bytes)

            if message_id in known_message_ids:
                continue

            resume_filename, resume_bytes = _pick_resume_attachment(msg)
            if not resume_filename:
                skipped_no_resume += 1
                continue

            display_name, from_email = _from_for(msg)
            results.append({
                "message_id": message_id,
                "references": _references_for(msg),
                "subject": _subject_for(msg),
                "display_name": display_name,
                "from_email": from_email,
                "resume_filename": resume_filename,
                "resume_bytes": resume_bytes,
            })

        if skipped_known:
            print(f"Skipped {skipped_known} already-recorded email(s) via header-only check.", flush=True)
        if skipped_no_resume:
            print(f"Skipped {skipped_no_resume} subject-matching email(s) with no resume attachment.", flush=True)

        return results
    finally:
        try:
            imap.close()
        except imaplib.IMAP4.error:
            pass
        imap.logout()
