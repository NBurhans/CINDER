# Availability note

Availability is the spine of every score. A build that beats a boss with an item you
cannot hold for two more badges is a fiction. This is where that chain is strong and
where it is weak.

## Timing is Measured, not asserted

Each entry in the source's area array sits under a numeric key, and that key is the
**index into the cap table at which the entry becomes reachable**. Confirmed on eight
independent cases:

| Evidence | Reads |
|---|---|
| Old Rod at Pallet Town | gate 0 — the rod is given before the first gate |
| Good Rod at Pallet Town | gate 3 — Surge, in whose city it is given |
| Super Rod at Pallet Town | gate 9 — Koga, in whose city it is given |
| Surf at Pallet Town | gate 10 — the gate after Surf becomes available |
| Six documented post-game gifts | gate 17, and the documentation says POST-GAME |

The keyspace across all 221 areas is exactly 0–17, matching the 18 cap indices with
nothing outside it.

This matters because the previous target dated **120 of its 127 encounter maps** from a
published route order, carrying them as Asserted. Here all 3,551 world rows carry a
gate read from source, and `earliest_gate` is `UNK` on none of them.

## Rates are Asserted

The numeric key is the gate, so rates come from **slot position** instead. The ladders
are published in the documentation, not encoded in the source: grass 12 slots at
20/20/10/10/10/10/5/5/4/4/1/1, old rod 70/30, good rod 60/20/20, super rod
40/40/15/4/1, surf 60/30/5/4/1. Every table in the game matched its ladder's slot
count. `wild-smash` has no published ladder and its 5 rows carry `UNK`.

So on an encounter row the species, level band and slot index are Measured and the
rate beside them is Asserted. They are different tiers on the same line.

## Quantity was wrong, and it mattered more than it looked

The source carries no quantity field. Placements were recorded as one copy each,
against the explicit "quantity, literal" rule. The documentation annotates them
`[xN]`, and **271 placements are bulk grants** — Berry Juice ×10, Life Orb ×10,
Ability Pill ×306, Quick Ball ×153.

Three things were wrong downstream, all of them silent:

- The **scarcity gate** rejected nearly everything, since almost nothing could clear
  "purchasable, or three or more copies."
- **`item_dependence` was UNK on 83% of rows**, because there was rarely a
  reliably-obtainable alternative to compare against. It is now UNK on 0.4%.
- **I5 failed on 16 of 17 teams** against copy counts wrong by a factor of ten. With
  literal quantities it passes 17 of 17.

Quantities are Asserted — they exist only in the documentation.

## The open gap: difficulty mode

`mode_availability` is `UNK` on all 3,551 world rows. The source does not encode which
items, TMs and tutors exist in which difficulty mode; the conditionality is prose in
the official item sheet, which marks entries as unavailable in one mode or swapped for
another.

Consequence: **every recommended build in this bundle is mode-agnostic** and may hold
an item that does not exist in the canonical mode. This is the largest open risk in
the dataset, and closing it is a manual pass against the documentation that would
land as Asserted.

## Out of pool

157 species-forms have no reachable gate by any path: breeding-only babies whose
parents nothing models, code-redeemed legendaries documented only in the Mystery Gift
sheet, and the five the documentation lists as genuinely unobtainable. They are
retained in the species master with `earliest_gate = UNK` and excluded from every
ladder rather than scored at zero.
