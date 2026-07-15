# Indeed application tracker (Gmail → Google Sheet)

Runs once a day via GitHub Actions. Scans your Gmail inbox for application
emails (subject containing "apply for" or "application for", with a resume
attached) received since 2026-01-01, and for each new one appends a row to a
Google Sheet with the applicant's email, applied date, role (parsed out of
the subject line), phone number (extracted from their resume), and a link to
the resume file (uploaded to a Google Drive Shared Drive). Already-recorded
emails are never reprocessed or re-added. Emails matching the subject phrase
but with no resume attached are skipped, since real applications in this
inbox always have one attached.

The main sheet (first tab) only ever shows those 5 human-readable columns.
A second tab, **MessageIDs**, is created automatically and holds the actual
dedup key (Gmail's Message-ID per email) — you never need to open or edit
it, it just needs to keep existing so re-runs don't create duplicate rows.

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

### 4. Create the Google Sheet and a Drive Shared Drive

1. Create a new Google Sheet (any name). Share it with the service account's `client_email` as **Editor**.
   - The sheet ID is the long string in its URL: `https://docs.google.com/spreadsheets/d/<THIS_PART>/edit`.
2. In Google Drive, use **Shared drives** (left sidebar), not a regular "My Drive" folder — service accounts have no storage quota of their own, so uploading into a normal folder fails with `storageQuotaExceeded` even if it's shared with them. Files inside a Shared Drive are owned by the drive itself, which sidesteps that.
   - **Shared drives → New** → name it e.g. "Indeed Resumes".
   - Open it → **Manage members** → add the service account's `client_email` → role **Content Manager** (or higher).
   - The Shared Drive's ID is the long string in its URL when you open it: `https://drive.google.com/drive/folders/<THIS_PART>`.
3. Note: resumes uploaded there are given a "anyone with the link can view" permission so the link always works from the sheet. Keep that in mind since resumes contain personal data.

### 5. Add GitHub Actions secrets

In this repository: Settings → Secrets and variables → Actions → New repository secret. Add each of these:

| Secret name | Value |
|---|---|
| `GMAIL_ADDRESS` | your Gmail address |
| `GMAIL_APP_PASSWORD` | the 16-character app password from step 2 |
| `GCP_SERVICE_ACCOUNT_JSON` | paste the **entire contents** of the downloaded JSON key file |
| `SPREADSHEET_ID` | the sheet ID from step 4 |
| `DRIVE_FOLDER_ID` | the Shared Drive ID from step 4 |

### 6. Push this repo to GitHub and run it

Push this folder to a GitHub repository (can be private). Then:

- Go to the **Actions** tab → "Daily candidate sync" → **Run workflow** to trigger it manually the first time.
- Check the run's log to confirm it found and processed emails correctly.
- After that, it runs automatically every day at 03:17 UTC (edit the cron line in `.github/workflows/daily-sync.yml` to change the time).

## Resetting after a schema change (e.g. adding the Role column)

If you already had data saved under the old column layout, clear it out
before running again so old-format rows don't mix with new ones:

1. Open the main sheet tab → select all cells (Ctrl/Cmd+A) → Delete. The
   script will insert the correct new header automatically on the next run.
2. If a "MessageIDs" tab already exists from before, delete that whole tab
   (right-click its name at the bottom → Delete) — it'll be recreated fresh.
3. In the Drive Shared Drive, select all the previously uploaded resume
   files and delete them, so there are no orphaned files left over.
4. Run the workflow again — it reprocesses everything from 2026-01-01
   with the new columns.

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
