# app

`../index.html` is built by injecting a compressed payload into `app_template.html`.

```
python3 build_payload.py     # phase outputs -> payload.b64 + sprites.b64
                             # then substitute both into app_template.html
```

## Interface

The layout, type and tier pills, dossier and per-checkpoint bar chart follow the survey
interface used for the previous target, unchanged in structure. Tabs: Dex, Rankings,
Roles, Teams, Starters, Bosses, Routes, About. Teams and Starters are new here.

Display faces are Newsreader over Archivo, requested from Google Fonts exactly as the
reference does. That is the one network request on the page; offline it falls back to
Georgia and Helvetica and the layout is unchanged.

## Why a payload rather than the TSVs

The valuation table is 105,084 rows and would not survive being embedded as text in a
file meant to open offline in one click. The Roles and Rankings tabs band and filter by role, so the payload carries **every**
scored (form, checkpoint, role) row — 105,064 of them — not one primary per form.
`build_payload.py` codes every repeated string (roles, tiers, items, natures, moves,
types, abilities, setup moves) to an integer and gzips the result: 12.57 MB of JSON
becomes 2.47 MB. Sprites are a separate payload at 2.80 MB.

Decompression uses the browser's native `DecompressionStream`, so no library ships
with the page. That costs compatibility below Chrome 80, Firefox 113 and Safari 16.4,
and the page says so rather than failing blank.

## What the interface deliberately does not do

No `localStorage`, no `sessionStorage`, no run state. The routes view is read-only:
it shows what a place holds and what that is worth, and there is nothing to tick off.
Missability is a property of the route, shown in place, not a task list.

## Deliberately blank

Fields the analysis does not compute are sent as null and render as em dashes rather
than being filled with invented numbers. Currently: nothing — `investment_cost`, ROI,
lineage value and the dead-weight penalty are all computed for this target.
