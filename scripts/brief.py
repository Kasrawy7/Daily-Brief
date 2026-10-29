#!/usr/bin/env python3
"""Validate and publish Daily World Brief editions.

  python3 scripts/brief.py validate [file.json ...]   check editions (default: data/latest.json)
  python3 scripts/brief.py publish new.json [--any-date]
        roll "previous", add calendar events, derive 5-session changes, validate,
        then write latest + archive. --any-date allows an edition not dated today (Cairo).
  python3 scripts/brief.py calendar [--from YYYY-MM-DD] [--days N]
        list verified upcoming events from data/calendar.json (default: next 14 days)

The site reads data/latest.json; data/archive/<iso>.json keeps every edition and
data/archive/index.json lists them for the edition picker.
"""
import datetime, json, re, sys, pathlib
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ARCH = DATA / "archive"

KEYS = ["edition", "notes", "previous", "top", "kpis", "chartGroups", "charts", "board",
        "chains", "categories", "stories", "week", "sources", "stocks"]
CATEGORIES = ["Global", "Middle East", "Egypt Economy", "Egypt Politics", "EGX Market",
              "Sectors & Companies", "Commodities", "Regulation"]
IMPS = {"Bullish", "Bearish", "Neutral"}
CONF = {"High", "Medium", "Low"}
VIZ = {"line", "hbar", "diverge", "split", "bullet"}
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
QUOTE = re.compile(r'"([^"]+)"')
STORY_TEXT = ("what", "why", "aff", "eg", "egx")
MOVE_TOL = 0.06      # max gap, in points, between a reported 1-day % and the one implied by the closes
BIG_MOVE = 10.0      # 1-day moves above this are flagged for a second look
WINDOW_DAYS = 14     # calendar events this close to the edition are added to "week"


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate(d):
    err = []
    for k in KEYS:
        if k not in d:
            err.append(f"missing key: {k}")
    if err:
        return err
    for s in strings(d):
        if "</" in s:
            err.append(f'string contains "</": {s[:60]}')
        if "—" in s:
            err.append(f"string contains an em dash: {s[:60]}")
    e = d["edition"]
    for k in ["date", "iso", "place", "preparedFor", "cutoffBadge"]:
        if k not in e:
            err.append(f"edition.{k} missing")
    if not ISO.match(e.get("iso", "")):
        err.append("edition.iso must be YYYY-MM-DD")
    for k in ["cutoff", "unverified", "sourcesFoot", "previous"]:
        if k not in d["notes"]:
            err.append(f"notes.{k} missing")
    if d["categories"] != CATEGORIES:
        err.append("categories changed")
    if [g.get("id") for g in d["chartGroups"]] != ["pulse", "macro", "context"]:
        err.append("chartGroups must be pulse, macro, context")
    if len(d["previous"]) > 5:
        err.append("previous has more than 5 editions")

    sids = [s.get("id") for s in d["stories"]]
    if len(sids) != len(set(sids)):
        err.append("duplicate story ids")
    sid = set(sids)
    for s in d["stories"]:
        for k in ["id", "cat", "imp", "key", "h", "src", "url", "date", "what", "why", "aff", "eg", "egx", "names"]:
            if k not in s:
                err.append(f"story {s.get('id')}: missing {k}")
        if s.get("cat") not in CATEGORIES:
            err.append(f"story {s.get('id')}: bad category {s.get('cat')}")
        if s.get("imp") not in IMPS:
            err.append(f"story {s.get('id')}: bad imp {s.get('imp')}")
    if not 3 <= len(d["top"]) <= 5 and d["stories"]:
        err.append("top must have 3-5 items")
    for t in d["top"]:
        if t.get("ref") not in sid:
            err.append(f"top ref not found: {t.get('ref')}")

    cids = [c.get("id") for c in d["charts"]]
    if len(cids) != len(set(cids)):
        err.append("duplicate chart ids")
    for c in d["charts"]:
        if c.get("group") not in ("pulse", "macro", "context"):
            err.append(f"chart {c.get('id')}: bad group")
        if c.get("ref") and c["ref"] not in sid:
            err.append(f"chart {c.get('id')}: ref not found {c['ref']}")
        for v in c.get("viz", []):
            if v.get("type") not in VIZ:
                err.append(f"chart {c.get('id')}: bad viz type {v.get('type')}")
            for p in v.get("points", []) + v.get("items", []) + v.get("parts", []):
                if not num(p.get("v")):
                    err.append(f"chart {c.get('id')}: non-numeric value {p.get('l')}")
            if v.get("type") == "bullet" and not (num(v.get("v")) and num(v.get("ref"))):
                err.append(f"chart {c.get('id')}: bullet needs numeric v and ref")
    for k in d["kpis"]:
        mini = k.get("mini")
        if mini:
            if mini.get("chart") not in cids:
                err.append(f"kpi {k.get('k')}: mini chart not found {mini.get('chart')}")
            else:
                ch = next(c for c in d["charts"] if c["id"] == mini["chart"])
                if mini.get("block", 0) >= len(ch.get("viz", [])):
                    err.append(f"kpi {k.get('k')}: mini block out of range")
    heroes = sum(1 for k in d["kpis"] if k.get("hero"))
    if heroes != 6:
        err.append(f"expected 6 hero KPIs, found {heroes}")

    for side in ("bull", "bear"):
        for b in d["board"].get(side, []):
            if b.get("ref") not in sid:
                err.append(f"board {side} {b.get('n')}: ref not found {b.get('ref')}")
            if b.get("c") not in CONF:
                err.append(f"board {side} {b.get('n')}: bad confidence {b.get('c')}")
    for w in d["week"]:
        if w.get("iso") and not ISO.match(w["iso"]):
            err.append(f"week {w.get('event')}: bad iso")
    for s in d["sources"]:
        if not (isinstance(s, list) and len(s) == 3):
            err.append(f"source must be [title, url, date]: {s}")

    sk = d["stocks"]
    for k in ["asOf", "iso", "histLabels", "indices", "equities", "note", "source"]:
        if k not in sk:
            err.append(f"stocks.{k} missing")
    for x in sk.get("indices", []):
        if not num(x.get("v")):
            err.append(f"index {x.get('n')}: v must be a number")
        for f in ("d", "w"):
            if x.get(f) is not None and not num(x[f]):
                err.append(f"index {x.get('n')}: {f} must be a number or null")
    tick = [e.get("t") for e in sk.get("equities", [])]
    if len(tick) != len(set(tick)):
        err.append("duplicate tickers in stocks")
    nh = len(sk.get("histLabels", []))
    for q in sk.get("equities", []):
        for f in ("t", "n", "sec", "px"):
            if f not in q:
                err.append(f"stock {q.get('t')}: missing {f}")
        for f in ("px", "d", "w"):
            if q.get(f) is not None and not num(q[f]):
                err.append(f"stock {q.get('t')}: {f} must be a number or null")
        h = q.get("hist", [])
        if h and (len(h) != nh or not all(num(v) for v in h)):
            err.append(f"stock {q.get('t')}: hist must have {nh} numbers to match histLabels")
        if h and num(q.get("px")) and abs(h[-1] - q["px"]) > 1e-9:
            err.append(f"stock {q.get('t')}: last hist value must equal px")
        # egx-data: the reported 1-day change must agree with the last two closes
        if len(h) >= 2 and all(num(v) for v in h) and h[-2] and num(q.get("d")):
            implied = (h[-1] / h[-2] - 1) * 100
            if abs(implied - q["d"]) > MOVE_TOL:
                err.append(f"stock {q.get('t')}: reported 1-day {q['d']}% disagrees with closes "
                           f"({h[-2]} to {h[-1]} implies {implied:.2f}%); recheck the page")
        if num(q.get("px")) and q["px"] <= 0:
            err.append(f"stock {q.get('t')}: px must be positive")
    if ISO.match(sk.get("iso", "")) and ISO.match(e.get("iso", "")) and sk["iso"] > e["iso"]:
        err.append("stocks.iso is after the edition date")

    # fact-check
    src_urls = {s[1] for s in d["sources"] if isinstance(s, list) and len(s) == 3}
    for s in d["sources"]:
        if isinstance(s, list) and len(s) == 3 and not (s[0].strip() and s[1].startswith("http") and s[2].strip()):
            err.append(f"source needs a title, an http(s) url and a date: {s}")
    for st in d["stories"]:
        if st.get("url") not in src_urls:
            err.append(f"story {st.get('id')}: its url is not in sources")
    for k in d["kpis"]:
        if k.get("hero") and " · " not in k.get("m", ""):
            err.append(f"hero kpi {k.get('k')}: m must be 'date · source'")
    for c in d["charts"]:
        has_derived = any(p.get("derived") for v in c.get("viz", [])
                          for p in v.get("points", []) + v.get("items", []) + v.get("parts", []))
        if has_derived and not c.get("derivedNote"):
            err.append(f"chart {c.get('id')}: has derived values but derivedNote is not true")
        if c.get("derivedNote") and "derived" not in c.get("cap", "").lower():
            err.append(f"chart {c.get('id')}: derivedNote is true but cap does not explain what is derived")
        if c.get("status") != "unverified" and c.get("viz") and not c.get("source"):
            err.append(f"chart {c.get('id')}: missing source")

    # house-style: at most one quote per story, each under 15 words
    for st in d["stories"]:
        quotes = [q for f in STORY_TEXT for q in QUOTE.findall(st.get(f, ""))]
        if len(quotes) > 1:
            err.append(f"story {st.get('id')}: {len(quotes)} quotes; use at most one per source")
        for q in quotes:
            if len(q.split()) >= 15:
                err.append(f"story {st.get('id')}: quote has {len(q.split())} words; keep it under 15")
    return err


def warnings(d):
    """Things that are allowed but deserve a second look before publishing."""
    w = []
    for q in d.get("stocks", {}).get("equities", []):
        if num(q.get("d")) and abs(q["d"]) >= BIG_MOVE:
            w.append(f"stock {q['t']}: 1-day move of {q['d']}%; confirm it in a second source")
    unv = [c["id"] for c in d.get("charts", []) if c.get("status") == "unverified"]
    if unv:
        w.append("unverified charts: " + ", ".join(unv))
    return w


def load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def dump(d, p):
    pathlib.Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def cairo_today():
    return datetime.datetime.now(ZoneInfo("Africa/Cairo")).date().isoformat()


def calendar_events(start, days):
    cal = DATA / "calendar.json"
    if not cal.exists():
        return []
    end = (datetime.date.fromisoformat(start) + datetime.timedelta(days=days)).isoformat()
    out = []
    for ev in load(cal):
        when = ev.get("iso") or ev.get("approx", "")
        if when and start <= when <= end:
            out.append(ev)
    return sorted(out, key=lambda ev: ev.get("iso") or ev.get("approx", ""))


def merge_calendar(new):
    """Drop past events from "week" and add verified calendar events due within WINDOW_DAYS."""
    iso = new["edition"]["iso"]
    before = len(new["week"])
    new["week"] = [w for w in new["week"] if not w.get("iso") or w["iso"] >= iso]
    dropped = before - len(new["week"])
    have = {(w.get("iso", ""), w.get("event", "").lower()[:24]) for w in new["week"]}
    added = []
    for ev in calendar_events(iso, WINDOW_DAYS):
        key = (ev.get("iso", ""), ev["event"].lower()[:24])
        if key not in have:
            new["week"].append({"date": ev["date"], "iso": ev.get("iso", ""), "event": ev["event"], "why": ev["why"]})
            added.append(ev["event"])
    new["week"].sort(key=lambda w: w.get("iso") or "9999")
    return dropped, added


def publish(newp, any_date=False):
    new = load(newp)
    today = cairo_today()
    if not any_date and new.get("edition", {}).get("iso") != today:
        print(f'Edition NOT published: edition.iso is {new.get("edition", {}).get("iso")} '
              f"but today in Cairo is {today}. Fix the date, or pass --any-date for a deliberate back-fill.")
        sys.exit(1)
    latest = DATA / "latest.json"
    if latest.exists():
        old = load(latest)
        if old["edition"]["iso"] != new["edition"]["iso"]:
            entry = {"date": old["edition"]["date"],
                     "items": [f'{t["what"]} → {t["why"]}' for t in old.get("top", [])]}
            prev = [p for p in new.get("previous", []) if p.get("date") != entry["date"]]
            new["previous"] = ([entry] + prev)[:5]
    dropped, added = merge_calendar(new)
    # The 5-session change is always derived from the closes, never typed by hand.
    for q in new.get("stocks", {}).get("equities", []):
        h = q.get("hist") or []
        if len(h) >= 2 and all(num(v) for v in h) and h[0]:
            q["w"] = round((h[-1] / h[0] - 1) * 100, 2)
    errs = validate(new)
    if errs:
        print("Edition NOT published:\n  " + "\n  ".join(errs))
        sys.exit(1)
    ARCH.mkdir(parents=True, exist_ok=True)
    dump(new, latest)
    dump(new, ARCH / f'{new["edition"]["iso"]}.json')
    idx = ARCH / "index.json"
    lst = load(idx) if idx.exists() else []
    lst = [x for x in lst if x["iso"] != new["edition"]["iso"]]
    lst.append({"iso": new["edition"]["iso"], "date": new["edition"]["date"]})
    lst.sort(key=lambda x: x["iso"], reverse=True)
    dump(lst, idx)
    print(f'Published {new["edition"]["date"]} ({len(new["stories"])} stories, '
          f'{len(new["stocks"]["equities"])} stocks).')
    if dropped or added:
        print(f"Week ahead: dropped {dropped} past event(s); added from calendar: {added or 'none'}")
    for w in warnings(new):
        print("Check: " + w)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "validate":
        files = sys.argv[2:] or [str(DATA / "latest.json")]
        bad = 0
        for f in files:
            d = load(f)
            errs = validate(d)
            print(f"{f}: " + ("OK" if not errs else "\n  " + "\n  ".join(errs)))
            for w in warnings(d):
                print("  check: " + w)
            bad += bool(errs)
        sys.exit(1 if bad else 0)
    elif len(sys.argv) >= 3 and sys.argv[1] == "publish":
        publish(sys.argv[2], any_date="--any-date" in sys.argv[3:])
    elif len(sys.argv) >= 2 and sys.argv[1] == "calendar":
        args = sys.argv[2:]
        start = args[args.index("--from") + 1] if "--from" in args else cairo_today()
        days = int(args[args.index("--days") + 1]) if "--days" in args else WINDOW_DAYS
        for ev in calendar_events(start, days):
            print(f'{ev.get("iso") or "approx " + ev.get("approx", "")}  {ev["event"]}  [{ev["source"]}]')
    else:
        print(__doc__)
        sys.exit(2)
