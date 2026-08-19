import email
import hashlib
import imaplib
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime

import config
import role_parser


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


def _applied_date_for(msg):
    date_header = msg.get("Date")
    if not date_header:
        return ""
    try:
        return parsedate_to_datetime(date_header).date().isoformat()
    except (TypeError, ValueError):
        return ""


def _from_email_for(msg):
    _, addr = parseaddr(msg.get("From", ""))
    return addr


def _subject_for(msg):
    raw = msg.get("Subject", "")
    try:
        return str(make_header(decode_header(raw)))
    except (ValueError, LookupError):
        return raw


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


def fetch_matching_applications(known_message_ids):
    """Connects over IMAP to every mailbox in config.MAILBOXES, searches each
    for application emails, and returns a combined list of dicts for messages
    not already present in known_message_ids. Each dict: message_id,
    from_email, applied_date, resume_filename, resume_bytes.
    """
    results = []
    for address, app_password in config.MAILBOXES:
        print(f"-- scanning {address} --", flush=True)
        try:
            results.extend(_fetch_from_mailbox(address, app_password, known_message_ids))
        except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError, TimeoutError) as exc:
            # A dropped/stalled IMAP session (Gmail closing a long-lived
            # connection, a network blip) shouldn't take the other
            # mailboxes down with it - log it and move on. SINCE_DATE never
            # rolls forward, so this mailbox's full range gets retried
            # automatically next run; nothing is lost, just delayed.
            print(f"  ! FAILED scanning {address}: {exc} - skipping for this run, will retry next run", flush=True)
    return results


def _fetch_from_mailbox(address, app_password, known_message_ids):
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, timeout=config.IMAP_TIMEOUT)
    try:
        imap.login(address, app_password)
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

            # SINCE_DATE never rolls forward, so most matched messages here
            # are ones already recorded on a past run. A full RFC822 fetch
            # downloads the whole email plus every attachment (e.g. resume
            # PDFs), so doing that for already-known messages just to throw
            # the result away wastes the majority of each run's time as the
            # mailbox grows. Check the Message-ID with a cheap header-only
            # fetch first and skip the full download when it's already known.
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

            # Real applications in this inbox always have a resume attached.
            # No attachment is a strong signal this is a job-alert digest or
            # newsletter that merely mentioned the subject phrase in passing.
            if not resume_filename:
                skipped_no_resume += 1
                continue

            subject = _subject_for(msg)
            results.append({
                "message_id": message_id,
                "from_email": _from_email_for(msg),
                "applied_date": _applied_date_for(msg),
                "role": role_parser.extract_role(subject),
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
