#!/usr/bin/env python3
"""After a push to main, wait for Vercel to serve the new edition.

  python3 scripts/check_live.py [--timeout 300]

Polls https://daily-brief-eg.vercel.app/data/latest.json until its edition date, stock
date, story count and update stamp (edition.update.ts) match data/latest.json, then exits 0. Exits 1 if the deploy does not show
up in time, so the routine can report it instead of claiming success.
"""
import json, pathlib, sys, time, urllib.request

SITE = "https://daily-brief-eg.vercel.app"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def key(d):
    e = d["edition"]
    return (e["iso"], e["date"], d["stocks"]["asOf"], len(d["stories"]), (e.get("update") or {}).get("ts"))


def main():
    args = sys.argv[1:]
    timeout = int(args[args.index("--timeout") + 1]) if "--timeout" in args else 300
    local = json.loads((ROOT / "data/latest.json").read_text(encoding="utf-8"))
    want = key(local)
    upd = local["edition"].get("update") or {}
    label = f' update {upd["n"]} ({upd.get("stage")}, {upd["at"]} Cairo)' if upd.get("n") else ""
    deadline, last = time.time() + timeout, None
    while time.time() < deadline:
        try:
            req = urllib.request.Request(f"{SITE}/data/latest.json?t={int(time.time())}",
                                         headers={"Cache-Control": "no-cache", "User-Agent": "brief-check"})
            live = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))
            got = key(live)
            if got == want:
                print(f"LIVE OK: {SITE} serves {want[1]}{label} ({want[3]} stories, stocks as of {want[2]})")
                return 0
            last = f"live site still serves {got[1]}, update stamp {got[4]} (stocks as of {got[2]})"
        except Exception as e:  # network blips and mid-deploy 404s are expected; keep polling
            last = f"fetch failed: {e}"
        time.sleep(15)
    print(f"LIVE NOT UPDATED after {timeout}s: {last}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
