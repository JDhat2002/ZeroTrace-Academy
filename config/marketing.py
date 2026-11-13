import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect

SKIP = {"login.html", "register.html"}


def marketing(request, page="index.html"):
    if page in SKIP or page.rstrip("/") in {"login", "register"}:
        target = "register" if "register" in page else "login"
        return HttpResponseRedirect(f"/{target}/")
    safe = Path(page).name
    if safe != page or not safe.endswith(".html"):
        raise Http404()
    file_path = settings.BASE_DIR / safe
    if not file_path.is_file():
        raise Http404()
    return HttpResponse(file_path.read_text(encoding="utf-8"))


def asset(request, path, root):
    base = (settings.BASE_DIR / root).resolve()
    target = (base / path).resolve()
    if base not in target.parents and target != base:
        raise Http404()
    if not target.is_file():
        raise Http404()
    content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return FileResponse(target.open("rb"), content_type=content_type)
