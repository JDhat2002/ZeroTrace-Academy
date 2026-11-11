# ZeroTrace Academy website

Django + Tailwind CSS + HTMX + vanilla JS homepage for ZeroTrace Academy.
Compiled CSS (`static/css/app.css`), fonts, icons and `htmx.min.js` are committed, so no CDN or Node runtime is needed to serve the site.

## Run locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver        # http://127.0.0.1:8000
python manage.py test core        # optional
```

SQLite is used by default. Set `POSTGRES_DB` (plus `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`) to switch to PostgreSQL. See `.env.example` for all settings; production requires `DJANGO_DEBUG=false` and `DJANGO_SECRET_KEY`.

## Front-end build (only when changing styles)

```bash
npm install
npm run build          # copy vendored assets (htmx, fonts) + compile Tailwind
npm run watch:css      # rebuild CSS while editing templates
python scripts/sync_icons.py   # after using a new Lucide icon name
```

## Layout

- `core/content.py`: all homepage content (departments, tools, roadmaps, plans and so on), shaped like future models. `core/services.py` is the only read path, so moving to the database only changes that file.
- `templates/sections/`: one template per homepage section. `templates/components/` holds reusable pieces (header, dropdown, cards, previews, pricing, FAQ, footer). `templates/partials/` holds the HTMX fragments (tool filter, roadmap tabs, AI mentor sample replies).
- `core/templatetags/zt.py`: the `{% icon %}` tag (inline Lucide SVGs from `core/icons/`), level helpers and JSON-LD.
- `static/js/main.js`: header state, dropdowns, mobile drawer, scroll reveal, collapsible lists, demo SOC stream and the hero canvas. Honours `prefers-reduced-motion`.

## Content rules

Tools are marked **Proposed**, the cyber range, CTF and AI mentor are labelled as previews or in development, dashboards show **demo data**, and testimonials and leaderboards are explicit placeholders. Statistics are computed from content (departments, tools, lab categories, paths), never typed in.
