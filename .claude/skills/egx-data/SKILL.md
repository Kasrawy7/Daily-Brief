---
name: egx-data
description: How to collect and verify EGX index closes, stock closes, investor flows, breadth and the EGP rate for the Daily World Brief. Use before filling the "stocks" block, the c-egx30, c-flows and c-breadth charts, or any EGX market figure.
---

# EGX data: sources, checks and known traps

The EGX trades **Sunday to Thursday**. Sessions close at 14:30 Cairo time. There is no session on Friday, Saturday or public holidays, so a Sunday edition's latest close is Thursday's.

## Source priority

| Data | Use first | Then | Notes |
| --- | --- | --- | --- |
| Stock closes and 1-day % | StockAnalysis history pages `https://stockanalysis.com/quote/egx/<TICKER>/history/` (WebFetch) | EGX's own site if it opens | Ask WebFetch for "the 6 most recent trading days: date, close, change %". Direct curl is blocked (403); WebFetch works. |
| EGX30 / EGX70 / EGX100 / EGX33 / EGX35-LV | Amwal Al Ghad "EGX closes..." / "stocks end week..." | Middle East Observer, See News, EnterpriseAM PM Edition, Arab Finance | Cross-check the EGX30 close in two sources. If they differ by more than 1 point, use neither and mark it unverified. |
| Investor flows by type | Middle East Observer (quotes Arab Finance / EGX data) | EnterpriseAM PM Edition | Report Egyptian / Arab / foreign, and individuals vs institutions when given. |
| Breadth, turnover, market cap | See News, Middle East Observer (Youm7 figures) | Amwal Al Ghad | |
| Debt flows (foreign/Arab T-bills, bonds) | Middle East Observer (Hapi data) | EnterpriseAM | Always state the cut-off time ("as of 4 pm"). |
| CBE EGP/USD | See News currency close | Arab Finance | Give buy and sell and the date. |

## Known traps (found in real runs)

- **Mansa Markets (mansamarkets.com/egypt) shows stale prices.** On 29 Oct its "26 Oct" prices were the 25 Oct closes. Do not use it.
- **Amwal Al Ghad's investor-flow figures sometimes use the wrong unit**, for example "42.259 billion pounds" for a figure that is clearly in millions. Use its index closes, but take flows from another source.
- **Ahram Online exchange-rate pages often show no date in search results.** Open the page and confirm the date before using it.
- **Search snippets are not sources.** Open the page and read the number on the page itself.
- **Sources conflict on flows quite often.** If two sources disagree on direction or size, leave the figure out and say so in `notes.unverified`.

## Building the `stocks` block

1. Pick the 6 most recent sessions shared by every ticker (oldest first) and write them as `histLabels`, e.g. `"Thu 22 Oct"`.
2. For each ticker, `hist` holds the 6 closes in that order, `px` is the last one, and `d` is the reported 1-day % from the page. Do not type `w`: the publish script derives it.
3. If a ticker's page fails or its dates do not line up, drop that ticker for the day and name it in `notes.sourcesFoot`. Never fill gaps from memory.
4. Index `w` (5-session change) is only allowed when you have a verified close from 5 sessions earlier. Set `wDerived: true` and explain it in `stocks.note`. Otherwise set it to `null`.

## What `scripts/brief.py` enforces

- Each stock's reported 1-day % must match its last two closes within 0.06 points. A mismatch usually means the page was read wrongly, or the dates are misaligned. Re-open the page; do not edit the number to fit.
- `hist` must have exactly as many values as `histLabels`, and the last value must equal `px`.
- 1-day moves of 10% or more are printed as "Check:" lines. Confirm each one in a news source before publishing. HDBK's +10.26% on 25 Oct was real.
