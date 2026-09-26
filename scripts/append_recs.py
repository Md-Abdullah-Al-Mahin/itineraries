#!/usr/bin/env python3
"""Serial-append rec rows to recs.csv. Reads a JSON array from stdin."""

from __future__ import annotations

import csv
import fcntl
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "london-paris" / "recs.csv"
FIELDS = [
    "city",
    "category",
    "priority",
    "name",
    "branch",
    "address",
    "area",
    "lat",
    "lng",
    "what",
    "source",
    "notes",
]
CATEGORIES = {
    "Museums",
    "Monuments",
    "Places of interest",
    "Restaurants",
    "Nightlife",
    "Bakeries & sweets",
    "Street food",
    "Parks",
    "Markets",
    "Streets",
    "Shops",
}


def canon_source(url: str) -> str:
    u = (url or "").strip()
    u = u.split("?")[0].rstrip("/")
    u = u.replace("/reel/", "/p/")
    return u


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("no stdin", file=sys.stderr)
        return 1
    payload = json.loads(raw)
    if isinstance(payload, dict):
        payload = [payload]
    rows = [r for r in payload if isinstance(r, dict) and "error" not in r]
    errors = [r for r in payload if isinstance(r, dict) and "error" in r]
    for err in errors:
        print(f"skip: {err['error']}", file=sys.stderr)

    with CSV_PATH.open("a+", newline="", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        existing = list(csv.DictReader(f))
        sources = {canon_source(r.get("source", "")) for r in existing}
        keys = {
            (r.get("name", ""), r.get("branch", ""), canon_source(r.get("source", "")))
            for r in existing
        }
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        added = 0
        for row in rows:
            if row.get("city") not in {"London", "Paris"}:
                continue
            if row.get("category") not in CATEGORIES:
                continue
            row.setdefault("priority", "random")
            src = canon_source(row.get("source", ""))
            row["source"] = src
            key = (row.get("name", ""), row.get("branch", ""), src)
            if key in keys:
                continue
            writer.writerow({k: row.get(k, "") for k in FIELDS})
            keys.add(key)
            sources.add(src)
            added += 1
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    print(f"appended {added} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
