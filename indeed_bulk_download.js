// Indeed bulk resume downloader + candidate data scraper (v4)
// Captures: Name, Email, Phone, Resume Downloaded (Yes/No), Apply Date, Profile
// Link, and now a Google Drive link to the uploaded resume file.
//
// ONE-TIME SETUP (Google Drive upload):
// 1. Go to https://console.cloud.google.com/ and create a project (any name).
// 2. APIs & Services > Library > search "Google Drive API" > Enable.
// 3. APIs & Services > OAuth consent screen > User type "External" > fill in
//    app name + your email > Save and continue through Scopes (no changes
//    needed) > on the Test users step, add the Google account whose Drive you
//    want the resumes saved to > Save.
// 4. APIs & Services > Credentials > Create Credentials > OAuth client ID >
//    Application type "Web application" > under "Authorized JavaScript
//    origins" add exactly: https://employers.indeed.com > Create.
// 5. Copy the Client ID (ends in .apps.googleusercontent.com) and paste it
//    into DRIVE_CLIENT_ID below, replacing the placeholder.
// You'll see a "Google hasn't verified this app" warning the first time you
// authorize — that's expected for a personal project; click Advanced > Go to
// (app name). This only happens once per browser (token refreshes silently
// after that, for as long as the project stays in Testing mode).
//
// HOW TO USE:
// 1. Go to the candidate you want to START from (e.g. candidate "1 of 107") on
//    employers.indeed.com/candidates/view?id=...
// 2. Open DevTools Console: Cmd+Option+J (Mac) or Ctrl+Shift+J (Windows)
// 3. Paste this entire script and press Enter.
// 4. A blue "Connect Google Drive & Start" button appears in the top-right
//    corner of the page — click it. A Google popup will ask you to sign in
//    and authorize Drive access (only needs to happen once per session).
// 5. Chrome may also show a small popup near the address bar asking to allow
//    multiple downloads from this site — click "Allow". This only happens once.
// 6. Watch the console for progress. Do not close the tab or click away while
//    it runs.
// 7. When done, it automatically downloads a CSV named indeed_candidates.csv.
//
// NOTES:
// - Email is read from the resume text itself. Some candidates only show an
//   Indeed-relay address (something@indeedemail.com) instead of their real
//   email — that's what Indeed displays for them, not a script bug.
// - "Apply Date" is approximate: Indeed only shows relative text like
//   "Applied 4 hours ago" in the UI, with no exact timestamp anywhere in the
//   page. This script converts that to a calendar date at the moment it
//   runs, and keeps the original relative text alongside it for reference.
// - Resumes are uploaded into a Drive folder named by DRIVE_FOLDER_NAME
//   below (created automatically on first run). They are private to the
//   Google account that authorized — not shared publicly.
//
// INCREMENTAL RUNS:
// - The script remembers every candidate it has already processed (saved in
//   this browser's localStorage, scoped to employers.indeed.com). On a later
//   run it will NOT re-download the resume file, re-upload it to Drive, or
//   re-scrape data for a candidate it already has — it just skips past them
//   quickly. Only candidates it hasn't seen before get downloaded/uploaded.
// - The CSV it produces each run is the FULL merged list (old + new), so you
//   always get one up-to-date file, but old resume files are never
//   re-downloaded or re-uploaded.
// - To force a clean re-scrape of everyone, run `indeedClearDownloadCache()`
//   in the console first, then run this script again.

(async function () {
  const DELAY_BETWEEN_CANDIDATES_MS = 900;
  const MAX_WAIT_MS = 15000;
  const MIN_WAIT_BEFORE_NO_RESUME_MS = 6000;
  const POLL_MS = 300;
  const STORAGE_KEY = 'indeed_bulk_download_state_v1';
  const DRIVE_FOLDER_ID_STORAGE_KEY = 'indeed_drive_folder_id_v1';
  // If >0, stop once this many already-processed candidates are seen back to
  // back — safe only because Indeed's default list order puts new applicants
  // first. Leave at 0 (disabled) unless you're confident about that ordering.
  const EARLY_STOP_AFTER_CONSECUTIVE_KNOWN = 0;
  // Keep saving resumes to the local Downloads folder too, in addition to
  // Drive. Set to false once you trust the Drive upload and don't want local
  // copies piling up.
  const KEEP_LOCAL_DOWNLOAD = true;

  // --- Google Drive config -------------------------------------------------
  const DRIVE_CLIENT_ID = 'YOUR_GOOGLE_OAUTH_CLIENT_ID.apps.googleusercontent.com';
  const DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive.file';
  const DRIVE_FOLDER_NAME = 'Indeed Resumes';

  function getContainer() {
    return document.getElementById('candidateProfileContainer');
  }
  function getCounterText() {
    const el = Array.from(document.querySelectorAll('span'))
      .find(e => /^\d+\s+of\s+\d+$/.test((e.textContent || '').trim()));
    return el ? el.textContent.trim() : null;
  }
  function getNextButton() {
    return document.querySelector('[aria-label="Next candidate"]');
  }
  function getDownloadLink() {
    return document.querySelector('[data-testid="download-resume-moreActions"]');
  }
  function extractPhone(text) {
    const candidates = text.match(/\+?\d[\d\s\-]{7,15}\d/g) || [];
    for (const c of candidates) {
      const digits = c.replace(/\D/g, '');
      if (digits.length >= 10 && digits.length <= 13) return c.trim();
    }
    return '';
  }
  function extractEmail(text) {
    const m = text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
    return m ? m[0] : '';
  }
  function getAppliedRawText() {
    const li = document.querySelector('li[aria-selected="true"]');
    if (!li) return '';
    const m = li.textContent.match(/Applied\s+(.+)$/i);
    return m ? m[1].trim() : '';
  }
  function parseAppliedDate(relText) {
    if (!relText) return '';
    const now = new Date();
    if (/today/i.test(relText)) return now.toISOString().slice(0, 10);
    const m = relText.match(/(\d+)\s*(minute|hour|day|week|month)s?\s*ago/i);
    if (!m) return '';
    const n = parseInt(m[1], 10);
    const unit = m[2].toLowerCase();
    const msPerUnit = { minute: 60000, hour: 3600000, day: 86400000, week: 604800000, month: 2592000000 };
    const d = new Date(now.getTime() - n * msPerUnit[unit]);
    return d.toISOString().slice(0, 10);
  }
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  function getCandidateId() {
    try {
      const u = new URL(location.href);
      return u.searchParams.get('id') || location.href;
    } catch (e) {
      return location.href;
    }
  }

  function loadKnownMap() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return new Map();
      const arr = JSON.parse(raw);
      return new Map(arr.map(r => [r.id, r]));
    } catch (e) {
      console.warn('Could not read saved candidate cache, starting fresh.', e);
      return new Map();
    }
  }

  function saveKnownMap(map) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(map.values())));
    } catch (e) {
      console.warn('Could not save candidate cache (localStorage full?).', e);
    }
  }

  window.indeedClearDownloadCache = function () {
    localStorage.removeItem(STORAGE_KEY);
    console.log('Indeed download cache cleared. Next run will re-scrape and re-download/upload everyone.');
  };

  async function waitForReady() {
    const start = Date.now();
    let stableCount = 0, last = '';
    while (Date.now() - start < MAX_WAIT_MS) {
      const c = getContainer();
      const txt = c ? c.innerText : '';
      const hasDownload = !!getDownloadLink();
      const looksLoaded = txt && txt.length > 40 && !txt.includes('Loading page');
      if (looksLoaded && txt === last) stableCount++; else stableCount = 0;
      last = txt;
      if (stableCount >= 2 && (hasDownload || Date.now() - start > MIN_WAIT_BEFORE_NO_RESUME_MS)) {
        return true;
      }
      await sleep(POLL_MS);
    }
    return false;
  }

  function csvEscape(v) {
    if (v == null) return '';
    const s = String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function downloadCsv(rows) {
    const header = ['Name', 'Email', 'Phone', 'Resume Downloaded', 'Drive Resume Link', 'Apply Date', 'Apply Date (raw)', 'Profile Link'];
    const lines = [header.join(',')].concat(
      rows.map(r => [
        csvEscape(r.name), csvEscape(r.email), csvEscape(r.phone),
        csvEscape(r.resumeDownloaded), csvEscape(r.driveLink), csvEscape(r.applyDate), csvEscape(r.appliedRaw),
        csvEscape(r.url)
      ].join(','))
    );
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'indeed_candidates.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  // --- Google Drive helpers -------------------------------------------------

  function loadGsiScript() {
    return new Promise((resolve, reject) => {
      if (window.google && window.google.accounts && window.google.accounts.oauth2) return resolve();
      const s = document.createElement('script');
      s.src = 'https://accounts.google.com/gsi/client';
      s.onload = () => resolve();
      s.onerror = () => reject(new Error('Failed to load Google Identity Services script.'));
      document.head.appendChild(s);
    });
  }

  function getAccessToken() {
    return new Promise((resolve, reject) => {
      const client = window.google.accounts.oauth2.initTokenClient({
        client_id: DRIVE_CLIENT_ID,
        scope: DRIVE_SCOPE,
        callback: (resp) => {
          if (resp.error) reject(new Error(`Google auth failed: ${resp.error}`));
          else resolve(resp.access_token);
        },
      });
      client.requestAccessToken();
    });
  }

  async function ensureDriveFolder(token) {
    const cachedId = localStorage.getItem(DRIVE_FOLDER_ID_STORAGE_KEY);
    if (cachedId) {
      const check = await fetch(`https://www.googleapis.com/drive/v3/files/${cachedId}?fields=id,trashed`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (check.ok) {
        const data = await check.json();
        if (!data.trashed) return cachedId;
      }
    }
    const q = encodeURIComponent(`name='${DRIVE_FOLDER_NAME.replace(/'/g, "\\'")}' and mimeType='application/vnd.google-apps.folder' and trashed=false`);
    const listRes = await fetch(`https://www.googleapis.com/drive/v3/files?q=${q}&fields=files(id,name)`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const listData = await listRes.json();
    if (listData.files && listData.files.length) {
      localStorage.setItem(DRIVE_FOLDER_ID_STORAGE_KEY, listData.files[0].id);
      return listData.files[0].id;
    }
    const createRes = await fetch('https://www.googleapis.com/drive/v3/files?fields=id', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: DRIVE_FOLDER_NAME, mimeType: 'application/vnd.google-apps.folder' }),
    });
    if (!createRes.ok) throw new Error(`Could not create Drive folder: ${createRes.status} ${await createRes.text()}`);
    const created = await createRes.json();
    localStorage.setItem(DRIVE_FOLDER_ID_STORAGE_KEY, created.id);
    return created.id;
  }

  async function uploadBlobToDrive(token, folderId, filename, blob) {
    const metadata = { name: filename, parents: [folderId] };
    const form = new FormData();
    form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }));
    form.append('file', blob);
    const res = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,webViewLink', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) throw new Error(`Drive upload failed: ${res.status} ${await res.text()}`);
    return res.json();
  }

  function waitForStartClick() {
    return new Promise((resolve) => {
      const btn = document.createElement('button');
      btn.textContent = 'Connect Google Drive & Start';
      btn.style.cssText = 'position:fixed;top:20px;right:20px;z-index:2147483647;padding:12px 20px;'
        + 'background:#1a73e8;color:#fff;border:none;border-radius:6px;font-size:14px;font-weight:600;'
        + 'cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.35);';
      btn.onclick = () => {
        btn.disabled = true;
        btn.textContent = 'Connecting…';
        resolve(btn);
      };
      document.body.appendChild(btn);
      console.log('Click the "Connect Google Drive & Start" button (top-right) to begin.');
    });
  }

  // --- Main ------------------------------------------------------------------

  if (DRIVE_CLIENT_ID.startsWith('YOUR_GOOGLE_OAUTH_CLIENT_ID')) {
    console.error('Set DRIVE_CLIENT_ID at the top of the script to your real Google OAuth Client ID before running. See the setup steps in the file header comments.');
    return;
  }

  await loadGsiScript();
  const startBtn = await waitForStartClick();

  let accessToken, folderId;
  try {
    accessToken = await getAccessToken();
    folderId = await ensureDriveFolder(accessToken);
    startBtn.remove();
  } catch (e) {
    console.error('Google Drive authorization failed, aborting.', e);
    startBtn.remove();
    return;
  }

  const knownMap = loadKnownMap();
  console.log(`Loaded ${knownMap.size} previously processed candidate(s) from cache.`);

  let total = null;
  let guard = 0;
  let seenCount = 0;
  let newCount = 0;
  let skippedCount = 0;
  let consecutiveKnown = 0;

  while (true) {
    guard++;
    if (guard > 500) { console.warn('Safety stop: exceeded 500 iterations'); break; }

    const ok = await waitForReady();
    if (!ok) console.warn('Timed out waiting for a candidate to fully render, capturing what is there.');

    const counter = getCounterText();
    if (counter) {
      const m = counter.match(/(\d+)\s+of\s+(\d+)/);
      if (m) total = parseInt(m[2], 10);
    }

    seenCount++;
    const candidateId = getCandidateId();
    const previousRow = knownMap.get(candidateId);

    if (previousRow) {
      skippedCount++;
      consecutiveKnown++;
      console.log(`[${counter || seenCount}] SKIP (already processed) ${previousRow.name}`);
    } else {
      consecutiveKnown = 0;
      const container = getContainer();
      const heading = container ? container.querySelector('h1,h2,h3') : null;
      const name = heading ? heading.innerText.trim() : '(unknown)';
      const containerText = container ? container.innerText : '';
      const phone = extractPhone(containerText);
      const email = extractEmail(containerText);
      const appliedRaw = getAppliedRawText();
      const applyDate = parseAppliedDate(appliedRaw);
      const url = location.href;

      const dl = getDownloadLink();
      let resumeDownloaded = 'No';
      let driveLink = '';
      if (dl) {
        if (KEEP_LOCAL_DOWNLOAD) dl.click();
        try {
          const blob = await (await fetch(dl.href)).blob();
          const filename = dl.getAttribute('download') || `${name.replace(/[^a-z0-9]+/gi, '_')}.pdf`;
          const uploaded = await uploadBlobToDrive(accessToken, folderId, filename, blob);
          driveLink = uploaded.webViewLink || `https://drive.google.com/file/d/${uploaded.id}/view`;
          resumeDownloaded = 'Yes';
        } catch (e) {
          console.warn(`Drive upload failed for "${name}":`, e);
          resumeDownloaded = KEEP_LOCAL_DOWNLOAD ? 'Yes (local only, Drive failed)' : 'Upload failed';
        }
      } else {
        console.warn(`No resume file available for "${name}" — skipping.`);
      }

      knownMap.set(candidateId, { id: candidateId, name, email, phone, resumeDownloaded, driveLink, applyDate, appliedRaw, url });
      newCount++;
      console.log(`[${counter || seenCount}] NEW ${name} | ${email || '(no email)'} | ${phone || '(no phone)'} | ${driveLink || '(no drive link)'}`);
    }

    if (EARLY_STOP_AFTER_CONSECUTIVE_KNOWN > 0 && consecutiveKnown >= EARLY_STOP_AFTER_CONSECUTIVE_KNOWN) {
      console.log(`Stopping early: hit ${consecutiveKnown} already-processed candidates in a row.`);
      break;
    }

    const nextBtn = getNextButton();
    const isDisabled = !nextBtn || nextBtn.disabled || nextBtn.getAttribute('aria-disabled') === 'true';
    if (!nextBtn || isDisabled) {
      console.log('Reached the last candidate.');
      break;
    }
    if (total && seenCount >= total) {
      console.log('Processed all candidates according to the counter.');
      break;
    }

    nextBtn.click();
    await sleep(DELAY_BETWEEN_CANDIDATES_MS);
  }

  saveKnownMap(knownMap);

  const finalRows = Array.from(knownMap.values()).sort((a, b) => {
    if (a.applyDate && b.applyDate) return b.applyDate.localeCompare(a.applyDate);
    if (a.applyDate) return -1;
    if (b.applyDate) return 1;
    return 0;
  });

  console.log(`Done. ${newCount} new candidate(s) processed, ${skippedCount} already had resumes (skipped). CSV has ${finalRows.length} total.`);
  downloadCsv(finalRows);
})();
