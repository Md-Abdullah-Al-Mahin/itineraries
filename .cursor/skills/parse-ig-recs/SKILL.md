---
name: parse-ig-recs
description: Parses Instagram recs for the London & Paris trip. Use when the user pastes Instagram reel/post URLs, a list of IG links, or asks to add recs to recs.csv. Spawns one subagent per link; the parent orchestrator serial-appends rows.
---

# Parse Instagram recs

When the user pastes Instagram URLs, do **not** open them yourself in a long sequential browser loop.

## Orchestrator (this agent)

1. Extract unique `instagram.com` URLs.
2. Skip a URL if `london-paris/recs.csv` already has that `source` (strip `?hl=` and trailing slash when comparing).
3. Spawn **one** `Task` subagent per remaining URL (`subagent_type: generalPurpose`, `model: inherit`). **Max 5 workers running at once.** Queue the rest; as soon as a slot frees, start the next URL. Workers must **not** write `recs.csv`.
4. Collect JSON rec arrays. Append **in original URL order** via:

```bash
python3 scripts/append_recs.py
```

Pass a JSON array on stdin. One append call per worker, in queue order — never two writers at once.

5. Reply with a short per-link summary. Flag venues the worker could not name.

Tell the user once: Cursor Settings → Agents → Approvals & Execution → **Auto-review** or **Run Everything**, so they are not clicking Run for every worker tool call.

## Worker prompt (paste as the Task `prompt`)

```
You parse ONE Instagram post for a London+Paris trip recs list.

URL: <URL>

Do not write recs.csv. Do not log into Instagram.

1. Fetch oEmbed caption: curl -sL "https://www.instagram.com/api/v1/oembed/?url=<permalink>"
2. Open the URL in the browser. Watch the video / swipe carousel. Capture on-screen venue names.
3. If a place has multiple branches, record every current London/Paris branch. Skip closed sites.
4. Geocode address (Nominatim or official site).
5. Return ONLY a JSON array of objects with keys:
   city, category, priority, name, branch, address, area, lat, lng, what, source, notes

city: London or Paris. Drop anywhere else.
category: exactly one of
  Museums | Monuments | Places of interest | Restaurants | Nightlife | Bakeries & sweets | Street food | Parks | Markets | Streets | Shops
priority: random unless the post says must-do / unmissable — then must-do
Nightlife vs Restaurants: classify by the rec, not the building. Food rec (roast, burger, plates) → Restaurants even if it is a pub. Drinks, dancing, cabaret, club → Nightlife.
source: the canonical https://www.instagram.com/... URL (no ?hl=)
notes: specific dish, activity, date, time, price, booking, closed days. Extra branches: "Same rec; extra branch"

If no London/Paris venue can be named, return [] and a one-line reason in the JSON as
[{"error":"..."}] instead.
```

## CSV

Path: `london-paris/recs.csv`  
Header: `city,category,priority,name,branch,address,area,lat,lng,what,source,notes`
