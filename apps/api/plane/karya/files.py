# Karya (CWI Studio) — attachment type resolution. Kept here so upstream merges touch one call per view.
# SPDX-License-Identifier: AGPL-3.0-only
"""The web client detects a file's type from its first bytes. Text formats (CSV, TXT) have no signature and legacy
Office files report the generic OLE container, so the upload arrived with "" or application/x-cfb and was refused
(Excel upload bug, 5 Oct 2026). Resolve from the file name instead, but only ever return a type on the allowlist."""
import mimetypes
import os

from django.conf import settings

# Everyday files our clients attach that upstream's list misses.
EXTRA_MIME_TYPES = {
    "application/vnd.ms-excel.sheet.macroEnabled.12",         # .xlsm
    "application/vnd.ms-excel.sheet.binary.macroEnabled.12",  # .xlsb
    "application/vnd.ms-word.document.macroEnabled.12",       # .docm
    "text/x-csv",
    "application/csv",
    "image/heic",   # iPhone photos
    "image/heif",
    "video/3gpp",   # Android / WhatsApp video
    "video/x-m4v",
    "video/x-matroska",
}

# Extension -> canonical type, used when the client sends nothing useful.
EXTENSIONS = {
    ".csv": "text/csv", ".tsv": "text/plain", ".txt": "text/plain", ".md": "text/markdown", ".log": "text/plain",
    ".xls": "application/vnd.ms-excel", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12", ".xlsb": "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
    ".doc": "application/msword", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".docm": "application/vnd.ms-word.document.macroEnabled.12",
    ".ppt": "application/vnd.ms-powerpoint", ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet", ".odt": "application/vnd.oasis.opendocument.text",
    ".pdf": "application/pdf", ".json": "application/json", ".zip": "application/zip", ".rar": "application/x-rar",
    ".7z": "application/x-7z-compressed", ".heic": "image/heic", ".heif": "image/heif",
    ".mp4": "video/mp4", ".mov": "video/quicktime", ".m4v": "video/x-m4v", ".3gp": "video/3gpp", ".webm": "video/webm",
    ".mkv": "video/x-matroska", ".avi": "video/x-msvideo", ".mp3": "audio/mpeg", ".m4a": "audio/x-m4a", ".wav": "audio/wav",
}
# Generic types a signature sniffer reports for containers; the extension is more specific.
GENERIC = {"", "application/octet-stream", "application/x-cfb", "application/zip", "text/plain"}


def allowed_types():
    return set(settings.ATTACHMENT_MIME_TYPES) | EXTRA_MIME_TYPES


def resolve_attachment_type(file_type, name):
    """Return an allowed MIME type for this upload, or None to refuse it."""
    allowed = allowed_types()
    file_type = (file_type or "").strip().lower()
    ext = os.path.splitext(name or "")[1].lower()
    by_name = EXTENSIONS.get(ext) or mimetypes.guess_type(name or "")[0]
    if file_type in GENERIC and by_name in allowed:
        return by_name
    if file_type in allowed:
        return file_type
    return by_name if by_name in allowed else None
