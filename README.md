# Indeed application tracker (Gmail → Google Sheet)

Runs once a day via GitHub Actions. Scans your Gmail inbox for application
emails (subject containing "apply", "application", or "applicant") received
since 2026-01-01, and for each new one appends a row to a Google Sheet with
the applicant's email, applied date, phone number (extracted from their
resume), and a link to the resume file (uploaded to a Google Drive folder).
Already-recorded emails are never reprocessed or re-added.

## One-time setup

### 1. Enable IMAP on the Gmail account

Gmail → Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP → Save Changes.

### 2. Create a Gmail App Password

1. You need 2-Step Verification turned on first: Google Account → Security → 2-Step Verification.
2. Google Account → Security → App passwords → create one (name it e.g. `indeed-tracker`).
3. Copy the 16-character password shown. You will not be able to view it again.

### 3. Create a Google Cloud service account

1. Go to console.cloud.google.com, create (or select) a project.
2. APIs & Services → Library → enable **Google Sheets API** and **Google Drive API**.
3. IAM & Admin → Service Accounts → Create Service Account (any name).
4. Open the new service account → Keys → Add Key → Create new key → JSON. This downloads a `.json` file — keep it private, never commit it.
5. Open the JSON file and note the `client_email` field (looks like `xxxx@xxxx.iam.gserviceaccount.com`).

### 4. Create the Google Sheet and Drive folder

1. Create a new Google Sheet (any name). Share it with the service account's `client_email` as **Editor**.
   - The sheet ID is the long string in its URL: `https://docs.google.com/spreadsheets/d/<THIS_PART>/edit`.
2. Create a Google Drive folder (e.g. "Indeed Resumes"). Share it with the same `client_email` as **Editor**.
   - The folder ID is the long string in its URL: `https://drive.google.com/drive/folders/<THIS_PART>`.
3. Note: resumes uploaded to this folder are given a "anyone with the link can view" permission so the link always works from the sheet. Keep that in mind since resumes contain personal data.

### 5. Add GitHub Actions secrets

In this repository: Settings → Secrets and variables → Actions → New repository secret. Add each of these:

| Secret name | Value |
|---|---|
| `GMAIL_ADDRESS` | your Gmail address |
| `GMAIL_APP_PASSWORD` | the 16-character app password from step 2 |
| `GCP_SERVICE_ACCOUNT_JSON` | paste the **entire contents** of the downloaded JSON key file |
| `SPREADSHEET_ID` | the sheet ID from step 4 |
| `DRIVE_FOLDER_ID` | the folder ID from step 4 |

### 6. Push this repo to GitHub and run it

Push this folder to a GitHub repository (can be private). Then:

- Go to the **Actions** tab → "Daily candidate sync" → **Run workflow** to trigger it manually the first time.
- Check the run's log to confirm it found and processed emails correctly.
- After that, it runs automatically every day at 03:17 UTC (edit the cron line in `.github/workflows/daily-sync.yml` to change the time).

## Running locally (optional, for testing)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export GMAIL_ADDRESS="you@gmail.com"
export GMAIL_APP_PASSWORD="xxxxxxxxxxxxxxxx"
export GCP_SERVICE_ACCOUNT_JSON="$(cat /path/to/service_account.json)"
export SPREADSHEET_ID="your-sheet-id"
export DRIVE_FOLDER_ID="your-folder-id"

python src/main.py
```

## Adjusting the subject keywords or start date

Edit `SUBJECT_KEYWORDS` and `SINCE_DATE` in `src/config.py`.
