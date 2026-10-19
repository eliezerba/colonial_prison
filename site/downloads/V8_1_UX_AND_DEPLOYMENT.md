# v8.1 — Design, UX and GitHub Pages

- Rebuilt navigation styling and information hierarchy as a restrained, legible editorial research interface.
- Added searchable command palette for seven views, all Palestine chart cards, and other section headings, plus Ctrl+K shortcut.
- Added contextual breadcrumb, quick user guide, topic section introduction, clearer active navigation and responsive mobile layout.
- Preserved all existing chart IDs, sections, forms, download generation, and data/mapping logic from v8.
- Added authentic Elijah Lab SVG sourced from the lab logo folder in connected Drive (SVG/logo.svg); self-hosted in site/assets.
- Root index.html redirects to site/index.html for local/repository browsing. Production Pages publishes site/ directly, where index.html is at document root.
- All file references use relative paths; no external JS or font CDN required.
- UX sources in ui are copied to site by enrichment rebuild, including new assets.
- v8.1 retains the known caveats of v8 data: comparison restrictions and unresolved source differences.
