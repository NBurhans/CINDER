# Manifest

Every file in the repository, what it holds, and what it is worth trusting.

## data/

| File | Rows | Contents |
|---|---|---|
| `01_species.tsv` | 1,343 | species-form master — identity, stats in display order, movepools, availability, gates |
| `01b_moves.tsv` | 1,003 | the move table: power, type, accuracy, PP, priority, split, TM and tutor slots |
| `01c_availability.tsv` | 2,546 | availability flattened out of the species master, one row per obtainment record |
| `01d_map_gates.tsv` | 195 | one row per place: when it opens, on what evidence, and what it holds |
| `02_world.tsv` | 3,551 | one row per acquirable thing — encounters with rates, items, tutors, gifts, trades, raid dens |
| `03_trainers.tsv` | 928 | trainers × difficulty mode, rosters resolved, cap-relative levels expanded |
| `03b_checkpoints.tsv` | 18 | the eighteen-gate checkpoint graph with level caps and scored slot counts |
| `04_matchups.tsv` | 43,934 | measured ceilings: margin, chosen item, item dependence, setup success, switch-in rate |
| `04a_builds.tsv.gz` | 64,650 | generated builds across four tracks plus setup variants, with item candidates |
| `05_valuation.tsv.gz` | 105,084 | roles, VORP, tiers, ROI, sustain, team score — the headline table |
| `05b_lineage.tsv` | 570 | lineage aggregate with the dead-weight penalty and where each line comes online |
| `05c_teams.tsv` | 17 | the recommended six per checkpoint from beam search, with the I5 verdict |
| `checkpoints.yaml` | — | adapter config — the checkpoint spine, read from source rather than constructed |
| `item_catalog.json` | — | every item classified from its own in-game description text |
| `item_copy_counts.json` | — | literal copy counts behind the scarcity gate |
| `mechanics.yaml` | — | adapter config — generation switches every damage cell inherits |
| `modes.yaml` | — | adapter config — the difficulty-mode axis and which mode is scored |
| `typechart.json` | — | decoded type matchups; source ids are non-contiguous and Fairy is 23 |

## pipeline/

Numbered in dependency order; each stage reads the previous stage's output.

| Script | Stage |
|---|---|
| `01_parse_species.py` | Phase 1 — species-form master and its integrity log |
| `02_parse_world.py` | Phase 2 — the world table from the area array |
| `03_parse_trainers.py` | Phase 3 — trainers, mode split, sentinel level resolution, checkpoint graph |
| `04_item_catalog.py` | Phase 4 — held-item catalogue classified from description text |
| `05_data_layer.js` | Phase 4 — custom data layer; the calculator supplies mechanics, never data |
| `06_build_generator.py` | Phase 4 — four-track build generation with per-checkpoint move pools |
| `07_matrix.js` | Phase 4 — the 1v1 matrix, measured item selection, priority in speed order |
| `08_natures.js` | Phase 5 — nature enumeration measured against the roster |
| `09_sustain.js` | Phase 5 — the sustain axis, sequential lifebar, published as kit delta |
| `10_coverage.js` | Phase 5 — per-slot coverage feeding the team layer |
| `11_valuation.py` | Phase 5 — roles, gates before scores, VORP |
| `12_teams.py` | Phase 5 — beam search, marginal contribution, invariant I5 |
| `13_finalize.py` | Phase 5 — tiers, lineage with dead-weight, invariants, export |
| `14_export_tables.py` | derived reference tables and adapter config |

## tools/

| Path | What it is |
|---|---|
| `verify_calcs.js` | Reproduces engine damage against an independent implementation of the generation-9 formula |
| `audit_integrity.py` | Round-trip, cross-phase referential integrity, the UNK sweep, invariant I6, the sensitivity pass |
| `skill/` | The core analysis skill — target-agnostic, and what governs methodology in every phase |

## app/

| Path | What it is |
|---|---|
| `build_payload.py` | Reduces the phase outputs to the rows the interface reads, codes them to integers, gzips |
| `app_template.html` | The interface, with the payload substituted in to produce `index.html` |
| `README.md` | Why a payload rather than the TSVs, and what the interface deliberately does not do |

## docs/

| File | Contents |
|---|---|
| `VISION.md` | Scope. The reference point for disputes |
| `RUNBOOK.md` | The working prompt, shipped as a template with §0 emptied — the filled block is INTERNAL |
| `PHASE_GATES.md` | What each of the seven phase gates reported, including the defects each caught |
| `PHASE7_NOTES.md` | Interface decisions, and two results that look wrong and probably are not |
| `AVAILABILITY_NOTE.md` | Where availability timing is Measured, where it is Asserted, and the open mode gap |
| `INTEGRITY_RECORD.md` | The audit depth: sources, encodings, parse gotchas, invariants with overrides, corrections |
| `CONTRIBUTING.md` | The non-negotiable rules, and how to rerun the pipeline |
| `PUBLISHING.md` | Naming policy, the known dependency leak, and the pre-push checklist |
| `integrity_log_phase*.json` | Per-phase machine-readable integrity logs |

## Not in this repository

Per `docs/VISION.md` §9 these are INTERNAL and never commit: the extracted source database,
the documentation set, intermediate parse artifacts, the filled target configuration block, and
the target adapter skill — which names a specific source layout and is identifying in a way a
list of species names is not. `tools/skill/` is the *core* analysis skill, which is
target-agnostic and ships.
