import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _mimetype_for(filename):
    lowered = filename.lower()
    for ext, mimetype in _MIME_TYPES.items():
        if lowered.endswith(ext):
            return mimetype
    return "application/octet-stream"


def upload_and_share(credentials, folder_id, filename, data_bytes):
    """Uploads resume bytes into the shared Drive folder, makes it link-readable,
    and returns the webViewLink to store in the sheet."""
    drive = build("drive", "v3", credentials=credentials)

    # folder_id is expected to be a Shared Drive (or a folder inside one).
    # Files created there are owned by the Shared Drive itself, not by this
    # service account, which has no storage quota of its own for regular
    # "My Drive" uploads (Google returns storageQuotaExceeded otherwise).
    # num_retries makes the client automatically back off and retry on
    # transient errors, including "User rate limit exceeded" (403), which
    # shows up when uploading many resumes back-to-back in one run.
    media = MediaIoBaseUpload(io.BytesIO(data_bytes), mimetype=_mimetype_for(filename), resumable=False)
    file = drive.files().create(
        body={"name": filename, "parents": [folder_id]},
        media_body=media,
        fields="id,webViewLink",
        supportsAllDrives=True,
    ).execute(num_retries=5)

    drive.permissions().create(
        fileId=file["id"],
        body={"type": "anyone", "role": "reader"},
        supportsAllDrives=True,
    ).execute(num_retries=5)

    return file["webViewLink"]
