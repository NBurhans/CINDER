# CINDER — dataset bundle

**Classification:** EXTERNAL. The target's public name, source file layout and the RUNBOOK §0
block are INTERNAL and appear nowhere in this file.

This README **is** the Audit depth. Every number in the app and the workbook traces back through
here to a source record.

---

## 1. Sources and parse

| Source | Priority | Records | Tier it produces |
|---|---|---|---|
| Extracted runtime database (`data.js`, 4,602,537 bytes) | 1 | 16 top-level keys | `Measured` |
| Official documentation set (7 PDFs + 1 xlsx) | 2 | prose and ordering | `Asserted` |
| `@smogon/calc` fork v0.9.0 | 3 | **mechanics only** | makes every calc `Derived` |
| Model knowledge | 4 | hypothesis generation only | never a shipped value |

Parsed 2026-09-08. The database is a JavaScript object literal, not JSON; converted once with
Node and all sixteen top-level counts confirmed to round-trip.

| Key | Count | Key | Count | Key | Count |
|---|---|---|---|---|---|
| `species` | 1343 | `areas` | 221 | `natures` | 25 |
| `moves` | 1003 | `trainers` | 464 | `eggGroups` | 16 |
| `abilities` | 255 | `caps` | 18 | `splits` | 3 |
| `items` | 749 | `sprites` | 1333 | `evolutions` | 25 |
| `types` | 18 | `tmMoves` | 128 | `scaledLevels` | 4 |

---

## 2. Encoding conventions

| Convention | Format | Example |
|---|---|---|
| List | comma-separated | `4,7,12` |
| Key:value | comma-separated | `Tackle:1,Growl:3` |
| Grouped records | pipe-separated records, colon-separated fields | `Route 1:wild-day:0:2-4:0` |
| Not applicable | `NA` | |
| Empty but valid | `NONE` | |
| Unknown / absent from source | `UNK` | |
| Literal tab, newline, pipe | escaped `\t`, `\n`, `\|` | |

`NA`, `NONE` and `UNK` never collapse into each other. `NONE` is a measurement, `UNK` is a gap,
`NA` is a category error.

---

## 3. Parse gotchas, and what each costs if you get it wrong

1. **Stat arrays are `[HP, Atk, Def, Spe, SpA, SpD]`** — Speed in slot 4, not slot 6. Verified
   head-to-head against the calculator's independent table: position 3 matches Speed in 45 of 63
   discriminating species and SpA in 1. Reading it in display order gives every Pokémon in the
   game the wrong Speed and silently corrupts every speed-order determination.
2. **Levels 101–104 are sentinels**, resolved through `scaledLevels` as offsets from the
   checkpoint cap (103→+0, 102→−1, 101→−2, 104→−3). 139 canonical-mode trainers use them.
3. **`name` is not a unique key.** 198 catalogue numbers carry multiple records over 515 rows;
   forms live in `key`. Charizard, Charizard-Mega-X and Charizard-Mega-Y all have
   `name = 'Charizard'`.
4. **Boss names are not unique either.** 27 names shared across 127 records. Bosses are keyed on
   (cap, area, name).
5. **TM and tutor movepools store slot indices, not move IDs.** TM number N resolves through
   slot N−1. Verified: TM01 Close Combat, TM39 Rock Tomb, TM119 Draco Meteor, matching the sheet.
6. **The type keyspace is not contiguous** — ids 0–8, 10–17, 23. Index 9 is the unused `???`
   slot (one move, Struggle) and **Fairy is 23**. The matchup array is 24 long for this reason.
   Treating indices 18–23 as padding drops every Fairy interaction in the game.
7. **Area numeric keys are checkpoint gate indices**, not rate buckets. Rates come from slot
   position instead.

---

## 4. Confidence split

`Measured` — species, moves, abilities, items, types, areas, trainers, caps, all placements and
all gates, parsed directly from the database.
`Derived` — every damage figure, margin, role score, VORP, tier, sustain depth.
`Asserted` — encounter rate ladders, the egg-move tutor gate, species weights, and anything from
the documentation set without corroboration in the database.
`Inferred` — trainer strategy prose, the `cap[1]` reading, the roster `ability` slot convention.

---

## 5. Validation numbers

| Check | Result |
|---|---|
| Round-trip, all 8 TSVs | 0 ragged rows |
| Roster species resolving against the species table | 0 unresolved |
| Ceiling forms resolving against the species table | 0 unresolved |
| Ceiling items obtainable by their checkpoint | 0 violations |
| Damage engine vs independent gen-9 implementation | 12/12, 0.0% discrepancy |
| `cap[0]` vs published level caps | 18/18 |
| Matrix | 2,698,734 cells, 0 builds failed to construct |

---

## 6. Invariant report

| # | Invariant | Threshold | Observed | Result |
|---|---|---|---|---|
| I1 | No held item in >25% of recommended builds | ≤0.25 | **0.3234** (Life Orb) | **FAIL — overridden** |
| I2 | No nature in >20% | ≤0.20 | **0.2612** (Adamant) | **FAIL — overridden** |
| I3 | mean \|r\| VORP vs BST within (checkpoint, role) | ≤0.60 | 0.5698 | PASS |
| I4 | Every (checkpoint, role) has ≥3 within 10% of leader | ≥3 | **35 of 252 cells fail** | **FAIL — overridden** |
| I5 | Recommended teams simultaneously equippable | 100% | **17/17 teams** | PASS |
| I6 | ±15 stat perturbation changes the build for ≥20% | ≥0.20 | 0.2074 | PASS |
| I7 | No move in >30% of recommended movesets | ≤0.30 | 0.1959 (Toxic) | PASS |

I3 is the **mean of within-cell correlations**, not a global one, computed over 216 cells with
n≥20; 36 cells below that floor are excluded and reported separately (their mean 0.598). A
Pearson r over five builds is noise, not evidence.

### Overrides

A failing invariant blocks release until fixed **or explicitly overridden in writing**. Three
overrides are in force.

**I1 — item concentration, observed 0.3234, worst Life Orb.**
Why acceptable: items are chosen by *measurement*, not by rank — every build's top three
candidates are run against that checkpoint's roster and the winner is whichever performs best.
Measurement changed the pick on 16.2% of builds. Life Orb dominates because setup builds want a
raw multiplier and it genuinely is their best item. Demoting it to satisfy the threshold would
mean publishing a build we measured to be worse.
What would fix it: a wider early-game offensive item pool, which is the target's design, not the
model's.

**I2 — nature concentration, observed 0.2612, worst Adamant.**
Why acceptable: tested. The candidate set was widened from 3 to 6 natures per track and
re-measured against the rosters; I2 moved only 0.286 → 0.261 and **18 distinct natures** are now
chosen, with a real tail down to three builds. The concentration is a property of the target, not
of a narrow shortlist.
What would fix it: nothing in the model. Adamant dominating physical attackers under an enforced
level cap is the target behaving as designed.

**I4 — 35 of 252 (checkpoint, role) cells lack three options within 10% of the leader.**
Why acceptable: the failures concentrate at checkpoints with genuinely tiny authored rosters —
Giovanni-2, Giovanni-3, Clair and Brendan each have exactly one authored boss and six scored
slots. With so few slots the leader's margin is easy to isolate.
What would fix it: nothing available. Per the vision these cells are named individually rather
than aggregated; see `INT_integrity_log_phase5.json`.

---

## 7. Model parameters

```
role_fit   = 0.25*S + 0.20*T + 0.15*Y + 0.40*F      (offence and defence families)
role_fit   =           0.30*T + 0.20*Y + 0.50*F      (utility family — see below)
replacement = role_fit of the third-best ZERO-INVESTMENT build in that (checkpoint, role)
VORP       = role_fit − replacement
tiers      = S+ ≥ +0.20 · S ≥ +0.12 · A ≥ +0.05 · B ≥ −0.02 · C ≥ −0.15 · D ≥ −0.35 · F below
dead-weight penalty = 0.50 on every checkpoint a lineage spends below replacement
```

**Why the utility family has no stat term.** Scoring utility roles on a stat made the cell a BST
ranking by construction: the core stat was raw HP, which tracks BST, and `T` was near-constant
because most pivots carry exactly one pivot move. Removing it took I3 from 0.641 to 0.570. This is
a design statement — utility roles are defined by tools and fight relevance, not by stats.

Tier distribution, curve **not** forced: S+ 2.4% · S 4.2% · A 7.2% · B 12.2% · C 25.9% ·
D 29.3% · F 18.9%.

---

## 8. Known limits

- **`mode_availability` is `UNK` on all 3,551 world rows.** The database does not encode
  difficulty-mode conditionality; it exists as prose in the official item sheet. Every ceiling is
  currently mode-agnostic and may hold an item absent in the canonical mode. **Highest open risk
  in the bundle.**
- **157 species-forms have no reachable gate** and are out of pool: breeding-only babies,
  Mystery-Gift legendaries, and the five the documentation lists as genuinely unobtainable.
- **Team coverage may be too easy.** Every checkpoint's recommended team reaches 100% threat
  coverage, because "covers a threat" means one member beats it 1v1. That is a low bar for
  "answers it" and the measure should be tightened before the number is trusted.
- **Sustain recomputes turns-to-KO** rather than reading them off the matrix cells, because Phase
  4 stored aggregates rather than per-slot data. Same engine, same inputs, second implementation
  — precisely the duplication §4.5a warns about.
- **Recovery constants (0.25 / 0.11 / 0.0625) are inherited from SABLE and were not re-derived**
  for this target's recovery pool.
- **Hazards score zero in the 1v1 primitive.** Their value is entirely about switching.
- **No AI model.** The database carries no trainer AI flags, so opponent switching is not
  modelled and deliberately so — any model of it would be invention.
- **`item_dependence` is `UNK` on 0.4% of rows** after the quantity correction below.
- **Species weights are Asserted** from the fork's bundled table (vanilla values), affecting
  Low Kick, Grass Knot, Heat Crash and Heavy Slam.

---

## 9. Corrections made

- Mega forms had no gate; now `max(base form gate, stone gate, Mega Ring gate)`. The Mega Ring
  sits at gate 8, which floors every mega regardless of when its stone appears. 225 unreachable
  forms → 157.
- Type effectiveness was built defender-side and read attacker-side; inverted and corrected.
- 56 species-forms, 70 moves, 1 ability and 3 items were being dropped by ID collision. Unfezant
  was the material one — two records at BST 503 and 478.
- The item catalogue produced zero `type_boost` and zero `resist_berry` on its first pass, and
  `species_locked` swallowed 145 items by matching "held by a **P**okemon".
- Move selection sorted on raw base power regardless of category, producing a special Mega
  Venusaur carrying Double-Edge. Now category-matched and STAB-weighted with a coverage rule.
- Egg moves were excluded from every pool; now gated at gate 9.
- Natures were a blanket `Hardy`, making I2 unmeasurable; now enumerated and measured.
- The `tank` gate was a stat filter wearing a role name; now requires real staying power.
- **Item quantities were recorded as 1 per placement**, against the runbook's explicit
  "quantity, literal" requirement. The database carries no quantity field; the official item
  sheet annotates them as `[xN]`, and 271 placement rows were bulk grants — Berry Juice ×10,
  Life Orb ×10, Ability Pill ×306. Consequences: the scarcity gate rejected almost everything,
  `item_dependence` was UNK on 83% of rows (now 0.4%), and I5 failed on 16 of 17 teams against
  a copy count wrong by a factor of ten. With literal quantities, **I5 passes 17/17**.
  Quantities are `Asserted` — they exist only in the documentation.

---

## 10. Files

| File | Rows | Contents |
|---|---|---|
| `01_species.tsv` | 1,343 | species-form master |
| `02_world.tsv` | 3,551 | encounters, items, tutors, gifts, trades, raid dens |
| `03_trainers.tsv` | 928 | trainers × mode, rosters resolved |
| `03b_checkpoints.tsv` | 18 | the checkpoint graph |
| `04a_builds.tsv` | 64,650 | generated builds across four tracks plus setup variants |
| `04_matchups.tsv` | 43,934 | measured ceilings with margin, item, setup and switch-in |
| `05_valuation.tsv` | 105,084 | roles, VORP, tiers, sustain |
| `05b_lineage.tsv` | 570 | lineage aggregate with dead-weight penalty |
| `INT_integrity_log_phase*.json` | — | per-phase integrity logs (INTERNAL) |

Nothing in this bundle is superseded.
