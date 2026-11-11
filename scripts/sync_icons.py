"""Copy the Lucide icons referenced by templates and content into core/icons/.

Usage (after `npm install`): python scripts/sync_icons.py
"""

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "node_modules" / "lucide-static" / "icons"
TARGET = ROOT / "core" / "icons"

PATTERNS = [
    re.compile(r"""\{%\s*icon\s+["']([a-z0-9-]+)["']"""),
    re.compile(r"""["']icon["']\s*:\s*["']([a-z0-9-]+)["']"""),
]


def referenced_icons():
    names = set()
    files = list((ROOT / "templates").rglob("*.html")) + [ROOT / "core" / "content.py"]
    for file in files:
        text = file.read_text()
        for pattern in PATTERNS:
            names.update(pattern.findall(text))
    return names


def main():
    if not SOURCE.exists():
        sys.exit("lucide-static not found; run `npm install` first.")
    TARGET.mkdir(parents=True, exist_ok=True)
    names = referenced_icons()
    missing = []
    for name in sorted(names):
        src = SOURCE / f"{name}.svg"
        if src.exists():
            shutil.copy(src, TARGET / src.name)
        else:
            missing.append(name)
    print(f"Copied {len(names) - len(missing)} icons to {TARGET.relative_to(ROOT)}")
    if missing:
        sys.exit(f"Missing icons: {', '.join(missing)}")


if __name__ == "__main__":
    main()
