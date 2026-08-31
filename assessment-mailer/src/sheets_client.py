import gspread

import config


def _open_spreadsheet(credentials):
    client = gspread.authorize(credentials)
    return client.open_by_key(config.SPREADSHEET_ID)


def open_sent_worksheet(credentials):
    spreadsheet = _open_spreadsheet(credentials)
    try:
        worksheet = spreadsheet.worksheet(config.SENT_SHEET_TITLE)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=config.SENT_SHEET_TITLE, rows=1000, cols=len(config.SENT_SHEET_HEADER))
        worksheet.insert_row(config.SENT_SHEET_HEADER, index=1)
        return worksheet

    first_row = worksheet.row_values(1)
    if first_row != config.SENT_SHEET_HEADER:
        worksheet.insert_row(config.SENT_SHEET_HEADER, index=1)
    return worksheet


def get_known_message_ids(sent_worksheet):
    column_values = sent_worksheet.col_values(1)
    return set(column_values[1:])  # skip header row


def normalize_email(address):
    """Lower-cased, trimmed form used as the per-candidate dedup key. Gmail
    treats the local part case-insensitively, and IMAP/header casing varies,
    so "Foo@Gmail.com" and "foo@gmail.com" must collapse to one key."""
    return (address or "").strip().lower()


def get_known_candidate_emails(sent_worksheet):
    """Every candidate email address that has already been sent an
    assessment (column 2 of the AssessmentsSent sheet). Once an address is
    in here it is never emailed another assessment again, even from a brand
    new application email / thread for the same or a different role - a
    person who already got a task is now a human-handled conversation."""
    column_values = sent_worksheet.col_values(2)
    return {normalize_email(v) for v in column_values[1:] if v.strip()}


def append_rows(worksheet, rows):
    if not rows:
        return
    worksheet.append_rows(rows, value_input_option="RAW")
