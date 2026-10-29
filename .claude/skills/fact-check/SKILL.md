---
name: fact-check
description: Source and number audit for the Daily World Brief. Use while writing stories, KPIs and charts, and as a final pass before publishing, so that every figure is traceable to an opened, dated source.
---

# Fact-check

The reader works in finance and relies on these numbers. A figure that is missing is better than a figure that is wrong.

## Rules for every number

1. **Opened, not snippeted.** Use a number only after opening the page that states it (WebFetch). Search-result summaries are leads, not sources.
2. **Dated.** Every KPI `m` reads `"<date of the figure> · <source>"`. Every story has `date`. Every source row is `[title, url, publication date]`.
3. **In the window.** Story sources must be published in the last 24 hours (the Sunday edition: since Thursday evening). Older pages may be used only as labelled context, for example "(context, 24 Oct)".
4. **One source is a report; two sources make it firm.** For the six headline tiles and the top story, look for a second source. If you only have one, keep the figure and name the single source.
5. **Conflicts are left out.** If two sources disagree, use neither. Name both in `notes.unverified`.
6. **Derived numbers are labelled.** Anything you calculate, such as a gap, a % change, a sum of flows or a real rate, gets `"derived": true` on the data point, `derivedNote: true` on the chart, and a caption that says what was calculated and from which inputs. In story text, write "(derived)" after the number.
7. **No memory figures.** Do not carry a number over from yesterday's edition unless you re-opened its source today. If you could not, list it in `notes.unverified`.

## Final pass before publishing

- [ ] Each story's `url` appears in `sources`. The script enforces this.
- [ ] Each number in `top` also appears in the referenced story.
- [ ] Each derived figure is tagged. The script enforces this for charts; check story text yourself.
- [ ] Each hero KPI `m` has a date and a source. The script enforces the format.
- [ ] `notes.unverified` lists every standard figure you could not verify today: flows, breadth, the 364-day T-bill yield, reserves, the budget oil price, the EGP rate.
- [ ] `notes.sourcesFoot` names pages you rejected and pages that failed to open.
- [ ] The edition date is today in Cairo. `publish` refuses any other date unless you pass `--any-date`, which is for deliberate back-fills only.
