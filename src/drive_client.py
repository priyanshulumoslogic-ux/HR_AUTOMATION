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

    media = MediaIoBaseUpload(io.BytesIO(data_bytes), mimetype=_mimetype_for(filename), resumable=False)
    file = drive.files().create(
        body={"name": filename, "parents": [folder_id]},
        media_body=media,
        fields="id,webViewLink",
    ).execute()

    drive.permissions().create(
        fileId=file["id"],
        body={"type": "anyone", "role": "reader"},
    ).execute()

    return file["webViewLink"]
