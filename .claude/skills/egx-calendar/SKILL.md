---
name: egx-calendar
description: Maintain data/calendar.json, the verified list of scheduled events (CBE MPC, CAPMAS inflation, FOMC, OPEC+, IPOs, earnings, IMF reviews, elections) that feeds the "Week ahead" section. Use when a story mentions a future date, or when "Week ahead" looks thin.
---

# EGX calendar

`data/calendar.json` is the memory of scheduled events across editions. When `scripts/brief.py publish` runs, it:

- drops "week" items whose `iso` is before the edition date;
- adds every calendar event due within 14 days that is not already in "week".

So you only write an event once; it then appears in each edition until its date passes.

## Entry format

```json
{
  "iso": "2026-12-17",
  "date": "Thu 17 Dec",
  "event": "CBE Monetary Policy Committee, last meeting of 2026",
  "why": "Why it matters for the EGX, one sentence.",
  "source": "Outlet, publication date",
  "url": "https://..."
}
```

For an event whose exact date is not confirmed, set `"iso": ""`, put the expected date in `"approx": "YYYY-MM-DD"`, and say "(date not confirmed)" in `date`. It is then shown without a countdown.

## Rules

- **Add only dates you have read on an opened page**, preferably the organiser's own: cbe.org.eg, federalreserve.gov, opec.org, capmas.gov.eg, egx.com.eg, imf.org. Fill in `source` and `url`.
- When an approximate date is confirmed, fill in `iso` and remove `approx`.
- When a date changes, edit the entry and update `source`.
- Delete entries more than 30 days in the past to keep the file short.
- Commit calendar changes together with the edition (`git add data`).

## Recurring events to look for each month

| Event | Usual timing | Where to confirm |
| --- | --- | --- |
| CAPMAS urban inflation | around the 9th–10th for the previous month | CAPMAS, CBE, Ahram, Daily News Egypt |
| CBE MPC | 8 meetings a year, on Thursdays | CBE press release; the next date is usually given in the decision coverage |
| CBE net international reserves | early in the month | CBE, Arab Finance |
| FOMC | 8 meetings a year | federalreserve.gov calendar |
| OPEC+ (seven-country group) | monthly, usually the first Sunday | opec.org press release |
| EGX earnings season | mid-month after quarter end | company disclosures on EGX |

## Check what is coming

```bash
python3 scripts/brief.py calendar --days 30
```
