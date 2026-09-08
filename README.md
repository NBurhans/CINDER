# halyard

A data-driven planning framework for turn-based RPG progression.

All 1,343 species forms scored by role against every boss roster at each of
eighteen checkpoints, from **2,698,734 damage-calculated matchups**.

**[Open the survey →](https://nburhans.github.io/halyard-cinder/)**

## What is here

| | |
|---|---|
| **`index.html`** | The survey — glance, dex, rankings, routes, starters, bosses. Self-contained, opens offline |
| **`data/`** | Analysis output as TSVs. `05_valuation.tsv.gz` is the headline: 105,084 scored rows |
| **`pipeline/`** | Every script, numbered in dependency order |
| **`app/`** | The payload builder and the app template |
| **`tools/`** | Verification suite — calc reproducibility, integrity audit, sensitivity and I6 |
| **`docs/`** | Vision, runbook template, the integrity record, per-phase integrity logs |

## How a build is scored

Roles first, gates before scores. A wall without recovery is not a wall at any
bulk. Every build is scored inside a role, never on one global ladder.

`role_fit = w_stat·S + w_tool·T + w_type·Y + w_fight·F`, all four reported.
Weights are `0.25 / 0.20 / 0.15 / 0.40`. The utility family carries **no stat
term** — `0.30 T / 0.20 Y / 0.50 F` — because scoring a pivot on raw HP made the
cell a base-stat ranking by construction. Removing it moved I3 from 0.641 to 0.570.

**Floor** is zero investment. **Ceiling** is the best build using only what is
obtainable by that checkpoint. **VORP** subtracts the third-best *floor* build in
the same role at the same checkpoint.

**Items are chosen by measurement, not by rank.** Each build's top three candidate
items are run against that checkpoint's roster and the winner is whichever
performs best. Measurement changed the pick on **16.2%** of builds.

**Setup moves generate their own build variant** and are evaluated with the boosts
applied, gated on surviving the setup turn. Of 15,997 builds offered both, the
setup variant wins on **9.6%** — and where it wins it is Shell Smash on Shuckle
and Belly Drum on Poliwhirl, which is the model finding real strategies rather
than being told about them.

**Priority orders turns.** Choice items are scored **under lock**, on one move
across the whole roster, at a mean cost of 0.37 margin.

**Sustain** is the turn dimension the damage axes cannot see: the roster walked
sequentially on one lifebar, the bar resetting at each trainer boundary, with
per-turn recovery counted. The published figure is the **kit delta**.

## What is trustworthy and what is not

Every damage figure is **Derived**, never Measured — generation 9 mechanics are
pinned and every cell inherits that. The engine was checked against an independent
reimplementation of the damage formula: **12/12 agreement, 0.0% discrepancy**.

Availability timing is **Measured**, not asserted. The source encodes a checkpoint
gate index on every area entry; the reading was confirmed against eight
independent cases including six post-game gifts landing on the final gate. All
3,551 world rows carry a real gate.

**Three of seven invariants fail and are overridden in writing** — each override
names the observed value, why it is acceptable, and what would fix it. I3 passes
at 0.570 against a 0.60 ceiling, I5 at 17/17, I6 at 0.207, I7 at 0.196. I1, I2 and
I4 do not pass. `docs/INTEGRITY_RECORD.md` lists every defect found and fixed,
including the ones that were mine.

The largest open risk is **difficulty-mode conditionality**, which the source does
not encode: every recommended build is mode-agnostic and may hold an item that
does not exist in the canonical mode.

Tier cuts are set numerically against this VORP distribution rather than
inherited, so they are not comparable to any earlier run's badges.

## Credits

Damage engine: [RadicalRedShowdown/damage-calc](https://github.com/RadicalRedShowdown/damage-calc),
used as a **mechanics engine only** — its bundled data layer is never used as data.

No ROM, save file or game asset is redistributed here. Derived tables only.
