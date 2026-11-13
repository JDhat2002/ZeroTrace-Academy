import uuid
from pathlib import Path

from django.conf import settings

from learning.services import LearningError

BLOCKED = {".exe", ".dll", ".js", ".html", ".htm", ".bat", ".cmd", ".ps1", ".sh", ".py", ".msi"}


def save_submission_file(upload, assignment):
    if upload is None:
        return "", ""
    original = Path(upload.name).name
    suffix = Path(original).suffix.lower()
    parts = Path(original).suffixes
    if any(part.lower() in BLOCKED for part in parts) or suffix in BLOCKED:
        raise LearningError("That file type is not accepted.", status=400)
    allowed = {f".{item.strip().lower()}" for item in assignment.allowed_extensions.split(",") if item.strip()}
    if suffix not in allowed:
        raise LearningError("That file type is not allowed for this assignment.", status=400)
    if upload.size > assignment.max_bytes:
        raise LearningError("The file is larger than the assignment allows.", status=400)
    root = Path(settings.SUBMISSION_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid.uuid4().hex}{suffix}"
    target = root / stored
    with target.open("wb") as handle:
        for chunk in upload.chunks():
            handle.write(chunk)
    return stored, original[:160]


def submission_file(stored_name):
    if not stored_name or "/" in stored_name or "\\" in stored_name:
        raise LearningError("That file is not available.", status=404)
    path = (Path(settings.SUBMISSION_ROOT) / stored_name).resolve()
    root = Path(settings.SUBMISSION_ROOT).resolve()
    if root not in path.parents or not path.is_file():
        raise LearningError("That file is not available.", status=404)
    return path
