# HR Assessment Mailer (Gmail → role-specific technical assessment)

Runs every 5 minutes via GitHub Actions (the shortest interval GitHub
Actions supports for scheduled workflows), so candidates get a reply
shortly after applying rather than waiting on a 6-hourly batch. Scans the
same inbox the [Indeed scraper](../src) in this same repo reads for
application emails (subject containing "apply for", "application for",
"intern", etc., with a resume attached), classifies the role from the
subject line, and — for the roles it knows — sends the candidate an
assessment email, using the candidate's name (pulled from their email's
display name, or their resume, or their email address as a last resort).

Every assessment email opens with the internship terms (3–6 month remote,
unpaid with a possible performance-based stipend) before the role message.
It's sent as an actual reply in the candidate's original thread (In-Reply-To
/References headers set, subject prefixed "Re:"), not a new standalone
email.

Only reacts to applications received from `SINCE_DATE` in `src/config.py`
onward — not the full mailbox history. Unlike the Indeed scraper (which
only ever adds spreadsheet rows and safely re-scans everything since Jan 1
every run), this script's mistakes are real emails sent to real people, so
it deliberately doesn't re-scan the whole inbox history each run.

Roles handled:

| Role (matched from subject) | Email | Attachment |
|---|---|---|
| QA Intern | QA assessment message | QA assessment PDF |
| Full Stack Intern | Full Stack assessment message | Full Stack PDF |
| Graphic Designer | Full-Stack-style message | Graphic Designer PDF |
| Recruiter Intern | Full-Stack-style message | Recruiter Intern PDF |
| AI Native Digital Marketing & Growth Intern | Video assessment message | none (doc + form links) |
| AI Native Sales & Business Development Intern | same video message | none (doc + form links) |

Applications for any other role, or ambiguous subjects that match more than
one role, are skipped and just logged to the run output — no email sent,
nothing recorded.

Each candidate only ever receives one assessment email: their Gmail
Message-ID is recorded in an **AssessmentsSent** tab on the same Google
Sheet the Indeed scraper uses, checked before sending on every run.

## One-time setup

### 1. Reuse the Indeed scraper's reading credentials

This reads the *same* inbox as the [Indeed scraper](../Indeed) (the one that
receives applications), so `READ_GMAIL_ADDRESS` / `READ_GMAIL_APP_PASSWORD`
should be set to the same values as that project's `GMAIL_ADDRESS` /
`GMAIL_APP_PASSWORD` secrets.

### 2. Sending mailbox: kiara.dave@lumoslogic.com

Assessment emails are sent from `kiara.dave@lumoslogic.com` (matches the
signature in the templates). You said you already have 2-Step Verification
and a Gmail App Password set up for this mailbox — just note the 16-character
App Password to add as a secret below. (If you ever need to redo it: Google
Account → Security → 2-Step Verification must be on, then Security → App
passwords → create one, e.g. named `hr-assessment-mailer`.)

### 3. Reuse the Indeed scraper's Google service account + spreadsheet

No new Google Cloud project needed. Reuse:
- The same service account JSON key used by the Indeed scraper (it already
  has Editor access to the spreadsheet, which is all this needs — it doesn't
  touch Drive).
- The same `SPREADSHEET_ID`. This script creates its own **AssessmentsSent**
  tab in it automatically on first run; it never touches the main tab or the
  `MessageIDs` tab the Indeed scraper owns.

### 4. Add GitHub Actions secrets

This lives in the same `HR_AUTOMATION` repo as the Indeed scraper (as the
`assessment-mailer/` subfolder), so it shares that repo's Settings → Secrets
and variables → Actions.

`GCP_SERVICE_ACCOUNT_JSON`, `SPREADSHEET_ID`, `GMAIL_ADDRESS`, and
`GMAIL_APP_PASSWORD` are **already set** (the Indeed scraper uses those
exact secret names, and the workflow maps `GMAIL_ADDRESS` /
`GMAIL_APP_PASSWORD` into `READ_GMAIL_ADDRESS` / `READ_GMAIL_APP_PASSWORD`
for this script) — nothing to do for those. Add only the 2 new ones, for the
separate mailbox this sends *from*:

| Secret name | Value |
|---|---|
| `SEND_GMAIL_ADDRESS` | `kiara.dave@lumoslogic.com` |
| `SEND_GMAIL_APP_PASSWORD` | the 16-character App Password for that mailbox |

### 4b. (Optional) Add a second, self-contained mailbox

For a second application inbox that should reply to candidates from
*itself* (e.g. `kiara.lumoslogic@gmail.com` reading its own applications
and sending its own assessment emails, rather than via the shared
`SEND_GMAIL_ADDRESS` sender above), reuse the same `GMAIL_ADDRESS_2` /
`GMAIL_APP_PASSWORD_2` secrets from the [Indeed scraper's README](../README.md#5b-optional-add-a-second-inbox-to-scrape)
— no new secrets needed here, this script picks them up automatically.
Candidates found in that mailbox get sent their assessment from that same
address, threaded into their original reply as normal. Dedup is tracked in
the same `AssessmentsSent` tab as the primary mailbox. Leave `GMAIL_ADDRESS_2`
unset and nothing changes — this only reads/sends via the mailbox above.

### 5. Run it

- Actions tab → "Send technical assessments (every 30min)" → **Run workflow**
  to trigger it manually the first time. Check the log to confirm it
  classified and sent correctly before trusting the schedule.

### 6. Set up the real 30-minute trigger (external cron)

GitHub's own `schedule:` trigger is unreliable at high frequency — it's
documented as best-effort, and in testing a `*/5 * * * *` schedule here
actually fired 1–3 hours apart. The workflow's built-in `schedule:` is kept
at a slow hourly cadence purely as a fallback safety net; the real 30-minute
cadence comes from an external service hitting GitHub's API directly.

A 30-minute interval was chosen over 5 minutes because cron-job.org's free
tier caps out at 2,000 executions/month — 5-minute ticks (~8,640/month) blow
through that cap partway through the month, while 30-minute ticks
(~1,440/month) stay under it:

1. **Create a GitHub Personal Access Token** (fine-grained):
   - GitHub → your profile picture → Settings → Developer settings →
     Personal access tokens → Fine-grained tokens → **Generate new token**.
   - Repository access: select **Only select repositories** → `HR_AUTOMATION`.
   - Permissions → Repository permissions → **Actions** → set to
     **Read and write**.
   - Generate, then copy the token (starts with `github_pat_...`) — you
     won't be able to view it again.
2. **Create a free account at [cron-job.org](https://cron-job.org)** (or
   any similar service that can POST on a schedule).
3. **Create a new cron job** there:
   - URL: `https://api.github.com/repos/priyanshulumoslogic-ux/HR_AUTOMATION/actions/workflows/send-assessments.yml/dispatches`
   - Method: `POST`
   - Headers:
     - `Authorization: Bearer <your token from step 1>`
     - `Accept: application/vnd.github+json`
     - `Content-Type: application/json`
   - Body: `{"ref": "main"}`
   - Schedule: every 30 minutes.
4. Save it, then check the repo's **Actions** tab — you should see new runs
   appearing roughly every 30 minutes, triggered as `workflow_dispatch`
   instead of `schedule`.

Each run is independent and re-scans/dedups against the `AssessmentsSent`
sheet, so a late or skipped tick (from either trigger) is never lost, just
picked up by the next one.

## Running locally (optional, for testing)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export READ_GMAIL_ADDRESS="you@gmail.com"
export READ_GMAIL_APP_PASSWORD="xxxxxxxxxxxxxxxx"
export SEND_GMAIL_ADDRESS="kiara.dave@lumoslogic.com"
export SEND_GMAIL_APP_PASSWORD="xxxxxxxxxxxxxxxx"
export GCP_SERVICE_ACCOUNT_JSON="$(cat /path/to/service_account.json)"
export SPREADSHEET_ID="your-sheet-id"

python src/main.py
```

**This actually sends real emails to real candidates** — there is no dry-run
mode. Test with a throwaway application email to yourself before relying on
the schedule.

## Adjusting role keywords, the form URL, or the assessment PDFs

- Role classification keywords: `src/role_classifier.py`.
- Submission form URL (same form for every role): `ASSESSMENT_FORM_URL` in
  `src/config.py`. AI Native "task details" doc: `AI_NATIVE_DOC_URL`.
- Internship terms paragraph prepended to every email: `TERMS_MESSAGE` in
  `src/config.py`.
- Email copy: `src/templates.py`.
- Assessment PDFs: replace the files in `assets/` (keep the same filenames,
  or update the paths in `src/config.py`).
