# Phase gates

Seven phases, each ending in a hard gate: row counts, the integrity log, the
validation numbers, then stop. What each gate actually reported.

---

## Phase 1 — species-form master

`01_species.tsv`, **1,343 rows × 47 columns**. Round-trips clean; BST equals the sum
of its parts on 1,343 of 1,343.

| Check | Result |
|---|---|
| Starters against the expected count | 27 / 27 |
| form_type | 1,078 base · 122 other · 76 regional · 67 mega |
| Zero level-up movepool | 0 |
| Unresolved evolution targets | 0 |
| Orphan learnset moves | 0 |
| Base stats outside 1–255 | 0 |
| Duplicate internal ids | 0 |
| No reachable gate | 225, later 157 |
| Species without a sprite | 20 |

**Stat-order verification, recorded as Measured.** Array position 3 matches the
calculator's independent Speed field on 45 of 63 discriminating species, and matches
SpA on 1. The exact-match rate across all six stats is only 32 of 63, which is
expected — this is a difficulty hack and value disagreements with a vanilla table are
the hack doing its job. The ordering is settled by the head-to-head, not the
exact-match rate.

**Three defects the gate caught.** `name` is not a unique key — 198 catalogue numbers
carry multiple records over 515 rows, and the first pass typed all 1,343 as `base`.
The dummy-slot heuristic flagged Ditto and Mew because "all six stats identical" is a
Gen-3 tell that does not hold here. The sprite table is not all species: three of its
keys are move-category icons.

### Correction, applied after the gate

Mega forms had no gate, because mega edges were excluded from the evolution parent
map. A mega's gate is now `max(base form gate, stone gate, Mega Ring gate)`. The Mega
Ring sits at gate 8, which floors **every** mega regardless of when its stone appears
— a stone-only rule would have placed 69 forms several gates too early. 225 → 157
unreachable.

---

## Phase 2 — world, items and interactions

`02_world.tsv`, **3,551 rows × 26 columns**.

| Entity type | Rows | | Entity type | Rows |
|---|---|---|---|---|
| wild_encounter | 2,228 | | item_care_package | 138 |
| item_ground | 365 | | gift_pokemon | 112 |
| vendor_stock | 296 | | tutor | 65 |
| raid_den | 167 | | static_pokemon | 20 |
| item_hidden | 141 | | roaming_pokemon | 10 |
| | | | trade_pokemon | 9 |

`earliest_gate` is **UNK on zero rows**. Every encounter table matched its published
rate ladder, so all 2,228 wild rows carry real slot rates; Route 1's day table sums to
exactly 100%. The only 5 UNK rates are `wild-smash`, which has no published ladder.

**Two independent corroborations.** TM numbering resolves through slot N−1 and lands
on Close Combat, Rock Tomb and Draco Meteor for TM01/39/119, matching the sheet. The
only two TMs with no placement anywhere in source are 107 and 118 — which the sheet
independently marks "CANNOT BE FOUND."

### Correction, applied at Phase 5b

Quantity was recorded as 1 per placement, against the explicit "quantity, literal"
requirement. 271 placements are bulk grants. See `AVAILABILITY_NOTE.md`.

---

## Phase 3 — trainers, bosses, checkpoint graph

`03_trainers.tsv`, **928 rows (464 normal / 464 hardcore)**. `03b_checkpoints.tsv`, 18.

| Check | Result |
|---|---|
| Roster slots, canonical mode | 1,531 |
| Level-scaled, canonical mode | 139 — parsed, flagged, never scored |
| Unresolved roster references | 0 species / 0 moves / 0 items |
| Duplicate trainer names | 27 names over 127 records |
| Cap curve monotonic | yes |
| Checkpoints with no roster of their own | 1 (Post-Game) |

**The caps blocker closed.** `cap[0]` matches the level cap published in the official
default-mode boss sheet on **18 of 18 gates**. `cap[1]` remains unidentified; the dex
tool's own filter code indexes caps by a `normal|hardcore` key, which makes
[normal, hardcore] the leading reading. Inferred, non-blocking.

**Type chart encoding resolved** — `0=×1, 5=×0.5, 20=×2, 1=×0` reproduces 12 of 12
known relations.

**Portability report: zero edits outside the target's own config.** Both things the
vision predicted would surface did — the mode axis and cap-relative level resolution —
and both sat behind adapter-level settings rather than forcing changes to shared logic.

---

## Phase 4 — build generation and the 1v1 matrix

`04a_builds.tsv` 64,650 builds; `04_matchups.tsv` 43,934 measured ceilings from
**2,698,734 cells**. Zero builds failed to construct.

**`mechanics_gen: 9` confirmed, not assumed** — 12 calcs spanning types, levels 20–85,
physical and special, STAB and neutral, reproduced against an independent
implementation of the generation-9 formula. 12/12 exact on both ends of the roll.

**Custom data layer**: 1,343 species / 1,003 moves / 255 abilities / 749 items / 18
types, every count matching source. It serves 185 moves and 1 species-form the fork's
bundled layer lacks, none substituted.

**Items are chosen by measurement.** Each build's top three candidates run against the
roster; the winner is whichever performs best. **Measurement changed the pick on 16.2%
of builds** — 4,526 of 27,937.

**Setup generates its own variant**, evaluated with boosts applied and gated on
surviving the setup turn. Of 15,997 builds offered both, setup wins on 9.6% — and
where it wins it is Shell Smash on Shuckle and Belly Drum on Poliwhirl.

**Priority orders turns.** Choice items score under lock, one move across the whole
roster, at a mean cost of 0.37 margin. Switch-in survivability is on every row; mean
safe rate 0.66.

### Defects found and fixed at this gate

The type chart was built defender-side and read attacker-side. 56 species-forms, 70
moves, 1 ability and 3 items were being dropped by ID collision — Unfezant was the
material one, two records at BST 503 and 478. The item catalogue produced zero
`type_boost` and zero `resist_berry` on its first pass, and `species_locked` swallowed
145 items by matching the phrase "held by a **P**okemon". Move selection sorted on raw
base power regardless of category, producing a special Mega Venusaur carrying
Double-Edge. Egg moves were excluded from every pool in the game.

---

## Phase 5 — valuation

`05_valuation.tsv` 105,084 rows · `05b_lineage.tsv` 570 lineages · `05c_teams.tsv` 17.

Weights `0.25 S / 0.20 T / 0.15 Y / 0.40 F`, utility family `0.30 T / 0.20 Y / 0.50 F`.
Dead-weight penalty 0.50. Tier cuts set numerically after seeing the VORP distribution.

Tier distribution, curve not forced: **S+ 2.4% · S 4.2% · A 7.2% · B 12.2% · C 25.9% ·
D 29.3% · F 18.9%**.

| # | Observed | Threshold | Result |
|---|---|---|---|
| I1 | 0.3234 (Life Orb) | ≤0.25 | FAIL — overridden |
| I2 | 0.2612 (Adamant) | ≤0.20 | FAIL — overridden |
| I3 | 0.5698 | ≤0.60 | PASS |
| I4 | 35 of 252 cells | 0 | FAIL — overridden |
| I5 | 17 of 17 teams | 100% | PASS |
| I7 | 0.1959 (Toxic) | ≤0.30 | PASS |

**I3 took three corrections to pass**, each right on its own merits rather than aimed
at the number: the `tank` gate was a stat filter wearing a role name; cells with n<20
were counting five-point correlations as evidence; and the utility family carried a
stat term whose core was raw HP, which made those cells a BST ranking by construction.
0.709 → 0.664 → 0.641 → 0.570.

The measurement underneath is sound: **raw margin correlates with BST at only 0.187**
per checkpoint, so the matrix is not a base-stat sort.

**I2 was unmeasurable until natures existed.** Every build carried `Hardy`. Natures are
now enumerated and measured against the roster; widening the candidate set from three
to six per track moved I2 only 0.286 → 0.261 and produced **18 distinct natures**, so
the concentration is the target rather than the shortlist.

---

## Phase 6 — evaluation

No new dataset. Everything re-read from disk.

| Check | Result |
|---|---|
| Round-trip, all TSVs | 0 ragged rows |
| Roster species resolving | 0 unresolved |
| Ceiling forms resolving | 0 unresolved |
| Ceiling items obtainable by their checkpoint | 0 violations |
| I6, ±15 perturbation | **0.2074** — PASS, narrowly |

I6 ran on a stratified sample of 135 forms across BST quartiles and evolution stage,
seed 20260908. It measures track reassignment only; item and move selection are
downstream of the track, so a stricter reading would test the whole build.

The sensitivity pass names **difficulty-mode conditionality** as the highest open risk
and the **role weights** as the highest-leverage judgment call — top-10 overlap between
weight profiles was 1 in 10 at the sample checkpoint.

---

## Phase 7 — companion app

`index.html`, 3.35 MB, single file, opens offline. Verified zero external URLs, zero
stylesheets, zero remote scripts, no `localStorage` or `sessionStorage`. The payload
was decoded back out of the shipped file to confirm it round-trips.

Seven tabs: Glance, Dex, Rankings, Routes, Starters, Bosses, and What to trust —
which carries the invariant table with its overrides and the known limits inside the
app rather than only in this repository.
