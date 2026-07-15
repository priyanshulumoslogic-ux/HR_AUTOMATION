import gspread

import config


def _open_worksheet(credentials):
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
    worksheet = spreadsheet.sheet1

    first_row = worksheet.row_values(1)
    if first_row != config.SHEET_HEADER:
        worksheet.insert_row(config.SHEET_HEADER, index=1)

    return worksheet


def get_known_message_ids(credentials):
    worksheet = _open_worksheet(credentials)
    column_values = worksheet.col_values(config.MESSAGE_ID_COLUMN)
    return worksheet, set(column_values[1:])  # skip header row


def append_rows(worksheet, rows):
    if not rows:
        return
    worksheet.append_rows(rows, value_input_option="RAW")
