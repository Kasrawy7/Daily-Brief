---
name: house-style
description: Writing style for the Daily World Brief (stories, top items, board calls, chains, captions). Use whenever writing or editing any text in data/latest.json.
---

# House style

The reader is Abdelrahman: Cairo-based, works in finance, reads on a phone between meetings. Write for someone who knows markets and has no time.

## Rules

- **Plain, direct English, present tense.** Write "The CBE raises rates", not "The CBE has raised" or "The CBE raised".
- **No em dashes, ever.** The publish script rejects them. Use a comma, a colon, a semicolon, or start a new sentence. En dashes are fine in ranges such as "3.75–4.00%".
- **EGP is the base currency.** Write "EGP 6.6 bn", "$391 mn", "EGP 56.20 per dollar". Use bn and mn, not billion and million.
- **Numbers carry their date** when it is not the edition day, for example "on Wednesday" or "in September".
- **Quotes:** at most one per source, under 15 words. The script enforces one per story. Otherwise summarise in your own words.
- **Directional, not advice.** Bullish and bearish calls read the news; they are not trade recommendations. Never write "buy", "sell", "target price" or "should".
- **Name names.** Use a specific EGX company when one is clearly affected, with its ticker if helpful, such as "Telecom Egypt (ETEL)". Fall back to a sector only when no single company is clearly hit.
- **Say what is unknown.** For example, "None of the sources gives a single cause." Do not invent a reason for a price move.

## Field lengths

| Field | Length |
| --- | --- |
| `top.what` | one sentence, at most about 30 words, with the key number |
| `top.why` | one clause starting in lower case; it renders after "→" |
| story `h` | headline, at most about 14 words, no full stop |
| story `what` | 2–4 sentences of facts with numbers |
| story `why`, `aff` | 1–2 sentences each |
| story `eg` | one line: the Egypt angle |
| board `r` | one line: the reason |
| chart `cap` | one or two sentences; explain any derived figure |

## Good examples (from the 29 Oct edition)

- what: "The CBE raises rates by 100 bp to a 20% deposit rate, its first hike since March 2024, when most analysts expected a hold"
  why: "the pound's slide past 56 and about $1.67 bn of foreign and Arab debt selling in three days (derived) push the CBE to defend the carry trade."
- Board: **Developers: TMG, Palm Hills**, driver "CBE hikes 100 bp": "A higher cost of credit raises financing costs for buyers and projects; TMG is down about 7.6% over five sessions (derived)."
- Honest gap: "The stock rises 4.87% on Thursday after 2.3% on Wednesday; no company-specific news is found, so this is a price read, not a cause."
