# Daily World Brief

A daily dashboard of world, Middle East and Egyptian news and what it means for
companies listed on the Egyptian Exchange (EGX). EGP base. Live at
**https://daily-brief-eg.vercel.app**.

## How it is built

| Path | What it is |
| --- | --- |
| `index.html` | The whole site: layout, styles and rendering code. It loads the edition from `data/`. |
| `data/latest.json` | The current edition. The daily routine replaces only this (through the script below). |
| `data/archive/<YYYY-MM-DD>.json` | Every published edition, opened with `?d=YYYY-MM-DD` or the Edition picker. |
| `data/archive/index.json` | The list of archived editions for the picker. |
| `scripts/brief.py` | Validates an edition and publishes it (rolls "previous", derives 5-session stock changes, archives). |
| `ROUTINE.md` | The instructions for the scheduled daily task. |
| `vercel.json` | Static hosting config: no caching on `data/` so a new edition shows at once. |
| `.github/workflows/validate.yml` | Checks every pushed edition against the schema. |

There is no build step: Vercel serves the files as they are.

## Sections

Market snapshot · Top stories · **EGX stocks and indices** (index cards, top movers,
and a sortable, filterable table of 21 blue chips with close, 1-day change,
5-session change, performance against the EGX30 and a 6-session trend line) ·
Charts · Bull / bear board · Connections · Story cards · Week ahead ·
Previous editions · Sources.

Every figure carries its date and source. Anything calculated rather than
reported carries a **derived** tag.

## Publish an edition by hand

```bash
python3 scripts/brief.py publish /path/to/new-edition.json
```

```bash
git add data && git commit -m "Edition 2026-10-29" && git push origin main
```

## Check the data

```bash
python3 scripts/brief.py validate
```

## Preview locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Deploy on Vercel (one-time setup)

1. Go to https://vercel.com/new and import the GitHub repository `kasrawy7/daily-brief`.
2. Set **Project Name** to `daily-brief-eg` (this gives the address `daily-brief-eg.vercel.app`).
3. Framework Preset: **Other**. Leave the build command and output directory empty; root directory is the repository root.
4. Click **Deploy**.
5. In **Settings → Git**, make sure the production branch is `main`. Every push to `main` then redeploys the site.
