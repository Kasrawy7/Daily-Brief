---
name: edition-qa
description: Quality checks for a Daily World Brief edition. Use before pushing (render test) and after pushing (confirm Vercel serves the new edition). Required on every daily run.
---

# Edition QA

Run these in order. Do not report success until every step passes.

## 1. Data checks (before commit)

```bash
python3 scripts/brief.py publish /tmp/new.json
```

This must print `Published ...`. Read every `Check:` line it prints, then either confirm the figure in a second source or remove it. Re-run the command after each fix.

## 2. Render check (before commit)

```bash
node scripts/smoke.js
```

This serves the repository locally and opens it in headless Chromium at desktop (1280px) and phone (390px) width. It fails on any of the following:

- script errors, or an edition that does not load;
- sideways page scroll on either width;
- fewer than 3 top stories, or not exactly 6 headline tiles;
- a story-card count or stock-row count that differs from the data;
- a chart that draws nothing;
- a masthead date that does not match `edition.date`.
- text cut off or overflowing in a headline tile, a tile mini chart taller than its strip, or a chart label running past the chart edge.

A hero KPI's `mini` may point only at a `line`, `bullet` or `split` chart; `brief.py` rejects any other type because it does not fit the tile.

If it fails, fix the data in `/tmp/new.json` and publish again. Never change `index.html` to make a check pass.

## 3. Commit and push

```bash
git add data && git commit -m "Edition YYYY-MM-DD" && git push origin main
```

## 4. Live check (after push)

```bash
python3 scripts/check_live.py --timeout 300
```

This polls `https://daily-brief-eg.vercel.app/data/latest.json` until the live edition date, story count, stock date and update stamp (`edition.update.ts`) match the local file, so a same-day update pass is only confirmed once Vercel serves it.

- `LIVE OK`: say the site is updated.
- `LIVE NOT UPDATED`: say so plainly in the one-line message, for example "pushed but Vercel has not deployed yet". Do not claim the site is updated.

Optionally run the render check against the live site:

```bash
node scripts/smoke.js https://daily-brief-eg.vercel.app/
```
