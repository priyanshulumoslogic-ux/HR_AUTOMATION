import gspread

import config


def _open_spreadsheet(credentials):
    client = gspread.authorize(credentials)
    return client.open_by_key(config.SPREADSHEET_ID)


def _open_main_worksheet(spreadsheet):
    worksheet = spreadsheet.sheet1
    first_row = worksheet.row_values(1)
    if first_row != config.SHEET_HEADER:
        worksheet.insert_row(config.SHEET_HEADER, index=1)
    return worksheet


def _open_dedup_worksheet(spreadsheet):
    # Message-IDs live on their own tab rather than as a visible column on
    # the main sheet, since they're purely a dedup key, not data a human
    # reading the sheet needs to see.
    try:
        worksheet = spreadsheet.worksheet(config.DEDUP_SHEET_TITLE)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=config.DEDUP_SHEET_TITLE, rows=1000, cols=1)
        worksheet.insert_row(config.DEDUP_SHEET_HEADER, index=1)
        return worksheet

    first_row = worksheet.row_values(1)
    if first_row != config.DEDUP_SHEET_HEADER:
        worksheet.insert_row(config.DEDUP_SHEET_HEADER, index=1)
    return worksheet


def open_worksheets(credentials):
    spreadsheet = _open_spreadsheet(credentials)
    main_worksheet = _open_main_worksheet(spreadsheet)
    dedup_worksheet = _open_dedup_worksheet(spreadsheet)
    return main_worksheet, dedup_worksheet


def get_known_message_ids(dedup_worksheet):
    column_values = dedup_worksheet.col_values(1)
    return set(column_values[1:])  # skip header row


def append_rows(worksheet, rows):
    if not rows:
        return
    worksheet.append_rows(rows, value_input_option="RAW")
