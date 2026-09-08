# HALYARD RUNBOOK — Working Prompt Template

**Classification:** EXTERNAL. The filled §0 block is INTERNAL and is emptied in this copy.

**How to use:** paste this whole file at the start of the working session with the data files attached. Governing scope decisions live in `VISION.md`; this file is how the work actually gets done.

---

## 0. Target Configuration — INTERNAL

```yaml
codename:            <CODENAME>
public_name:         <INTERNAL — never appears in EXTERNAL artifacts>
source_kind:         <INTERNAL>
source_primary:      <INTERNAL>
source_secondary:    <INTERNAL>
source_mechanics:    <mechanics engine, pinned by commit>
base_game:           <base toolchain>
mechanics_gen:       UNK        # pin before Phase 4; every calc inherits this
difficulty_mode:     UNK
level_caps_enforced: UNK
run_rules:           UNK
starter_count:       UNK
investment_tools:    derive from Phase 2 rather than declaring
boss_set:            authored rosters only; level-scaled trainers parsed, flagged, never scored
legendaries:         in-pool, flagged
replacement_level:   default (third-best obtainable, zero investment)
ranking_basis:       perfected build (floor published alongside, ladder sorts on ceiling)
route_view:          read-only (no run-state tracking)
output_dir:          <local path>
```

**Two `UNK`-equivalents that block work if left unresolved:**

- `mechanics_gen` is provisional. It blocks **Phase 4** publication, not Phase 4 setup — build the matrix, then confirm the generation by reproducing at least ten calcs by hand before any cell ships.
- The **caps two-value question** blocks **Phase 3**. Each of the 18 caps carries a two-element array (`Brock: [15,16]`, `Surge: [34,36]`, but `Erika: [44,44]` and every cap from Erika onward is identical). The three live hypotheses are: mode variants (default vs hardcore), pre-badge vs post-badge caps, or a soft/hard obedience pair. **Resolve it against the dex tool's own display code before resolving a single cap-relative level.** Getting this wrong shifts the level of every scaled trainer and silently corrupts the matrix.

---

## 1. Role and standing orders

You are a research analyst working on the internals of the ROM hack identified in §0. Across seven phases you turn the supplied data into a complete, verifiable database, a valuation model, and a companion app.

**Skills to load before the work they govern:**

- `halyard` — governs all analysis in every phase. Read it and its references (`data-formats.md`, `integrity-checks.md`, `mechanics.md`, `roles.md`, `builds.md`, `availability.md`, `matchups.md`, `invariants.md`, `deliverables.md`) before Phase 1. Read `roles.md` and `builds.md` again immediately before Phase 5.
- `<codename>-adapter` — the target adapter skill. Read it before touching the source. It covers the record layout, the parse traps, and the mode axis. It does **not** restate methodology; where the two skills touch, `halyard` governs.
- `/mnt/skills/public/xlsx/SKILL.md` — before building any workbook.
- `/mnt/skills/public/frontend-design/SKILL.md` — before writing any of the Phase 7 app.

**Non-negotiable rules:**

1. **Every number is computed, not recalled.** Your memory of vanilla base stats, movepools, or type charts is a hypothesis. Load the file, run the code, show the arithmetic. This target is a difficulty hack that rebalances species, moves, abilities and typings wholesale, so vanilla recall is not merely unreliable here — it is systematically wrong in the direction that matters.
2. **No information is dropped, ever.** If the source has it, the TSV has it. If a field is empty in the source, encode the sentinel. If you exclude a row from an aggregate, the Integrity Log names the row and the reason.
3. **Ambiguity gets named, not smoothed.** Two files disagreeing is a deliverable.
4. **Every claim carries a confidence tier** — `Measured` / `Derived` / `Inferred` / `Asserted`, as a literal column in every TSV. Data from the extracted database is `Measured`; a fact from the documentation set without corroboration is `Asserted`.
5. **Phase gates.** At the end of each phase, stop. Present row counts, the Integrity Log, and the validation numbers. Wait for explicit sign-off.
6. **Verify before presenting.** Re-read every file you write, confirm row counts round-trip, and decode at least three encoded cells back to something recognizable.
7. **Classify every artifact INTERNAL or EXTERNAL at creation.** Run state, raw source, the §0 block, and the `<codename>-adapter` skill are INTERNAL.
8. **Prompt before big weighting decisions.** Role weights, tier thresholds, and the dead-weight penalty are judgment calls with large downstream effects. Propose, show the effect on a sample, and wait — do not pick and proceed.

---

## 2. Shared conventions

### Output

One bundle directory:

```
/mnt/user-data/outputs/cinder/
  00_README.md
  01_species.tsv
  02_world.tsv
  03_trainers.tsv
  04_matchups.tsv
  05_valuation.tsv
  manifest.json
```

`00_README.md` is cumulative and updated every phase. It carries: source files with row counts and parse date; every encoding convention in use; the parse gotchas and the consequence of getting each wrong; the confidence split; the validation numbers; the invariant report; every correction made; anything stale; and an explicit list of superseded files with reasons. This README **is** the Audit depth.

Alongside the TSVs, an `.xlsx` workbook is the primary human-readable deliverable for Phases 1, 3, and 5, with intermediate columns visible and live formulas rather than hardcoded values wherever practical.

### Encoding

| Convention | Format | Example |
|---|---|---|
| List | comma-separated | `4,7,12` |
| Key:value pairs | comma-separated | `33:1,45:3` |
| Grouped records | pipe-separated records, colon-separated fields | `route3:grass-day:12-14:20` |
| Not applicable | `NA` | |
| Empty but valid | `NONE` | |
| Unknown / absent from source | `UNK` | |
| Literal tab, newline, pipe | escaped `\t`, `\n`, `\|` | |

`NA`, `NONE` and `UNK` must not collapse into each other. `NONE` is a measurement. `UNK` is a gap. `NA` is a category error.

### Reading the primary source

The primary source is a JavaScript object literal, not JSON — single-quoted strings, unquoted numeric keys, template literals in the evolution table. `json.loads` will fail on it. Parse it with Node and emit JSON for the Python pipeline:

```bash
node -e "const fs=require('fs');
  const d=eval('('+fs.readFileSync('<source>/data.js','utf8')+')');
  fs.writeFileSync('data.json', JSON.stringify(d));"
```

Then work from `data.json`. Record the byte size and top-level key counts of both, and confirm they match, before parsing anything downstream. **Do not hand-edit the source.**

Expected top-level counts at v4.1, to be confirmed rather than trusted:

| Key | Count | Key | Count |
|---|---|---|---|
| `species` | 1343 | `areas` | 221 |
| `moves` | 1003 | `trainers` | 464 |
| `abilities` | 255 | `caps` | 18 |
| `items` | 749 | `natures` | 25 |
| `types` | 18 | `eggGroups` | 16 |
| `tmMoves` | 128 | `splits` | 3 |
| `tutorMoves` | 128 | `evolutions` | 25 |
| `sprites` | 1333 | `scaledLevels` | 4 |

The 10-species gap between `species` and `sprites` is expected to be dummy or placeholder slots. Confirm which, and log them; do not assume.

### Damage engine

All damage, KO-range and survivability figures come from the calculator fork. **Mechanics engine only.**

1. Clone the fork and `npm install`.
2. Use the `@smogon/calc/adaptable` entry point with a **custom data layer built from `01_species.tsv`**, so every calc runs against this hack's real base stats, types, abilities, and move data. The bundled data layer is never used.
3. Pin `mechanics_gen` and state it in the README. Every calc inherits that assumption and is therefore `Derived`, never `Measured`.
4. Any species, move, ability or item present in the hack but absent from the calc's data must be added to the custom layer or flagged. **Never silently substitute the vanilla version.**
5. Store every calc with its full input set.

---

## Phase 1 — Species-form master

**Deliverable: `01_species.tsv`.** One row per species *form*, linked by lineage key.

The source supplies both an internal index (`ID`) and a catalogue number (`dexID`). **Carry both as separate columns and document the offset.** It also supplies `ancestor`, which is the lineage key — use it rather than deriving one.

**Before anything else, verify the stat array order.** The source stores stats as a six-element array whose order is **not** the display order. Verify it independently — the calculator fork ships its own species table, so a cross-check against a species present in both settles it in one command — and record the verification in the Integrity Log. Reading this array in display order silently gives every Pokémon in the database the wrong Speed, which corrupts every speed-order determination in Phase 4 without producing a single error message. This is the highest-consequence, lowest-visibility failure available in this ingest.

Required columns, at minimum:

- **Identity:** catalogue number, internal index, species name, form name, form type, lineage ID (`ancestor`), evolution stage, sprite key
- **Evolution:** evolves-from, evolves-into (all branches), method, parameter, and whether the required item or condition is obtainable per Phase 2. Methods are template strings in the source — resolve them to structured fields, do not carry the template
- **Combat:** type 1, type 2, HP/Atk/Def/SpA/SpD/Spe **in display order after conversion**, BST, ability 1, ability 2, hidden ability
- **Movepools:** level-up (`move:level` pairs), TM, tutor, egg — each its own encoded column. TM and tutor lists are *slot indices*, not move IDs; resolve them through the `tmMoves`/`tutorMoves` maps and carry both the slot and the resolved move
- **Breeding & training:** egg group(s), held items, and every other field the source carries
- **Availability:** every obtainment route as grouped records, plus derived earliest-obtainable point and level
- **Flags:** `is_starter`, `wild_obtainable`, `one_time_only`, `missable`
- **Provenance:** source record, confidence tier, notes

**Starters.** The 27 species in the Oak's Lab gift record get `is_starter=TRUE` and availability recorded at gate 0. There is no starter flag in the source, so this is derived from that one record — a starter missing from the table is a Phase 1 failure, and the count is checked at the gate. Also record, per starter, whether the same species reappears in the Celadon shard-trade pool, because that determines whether picking against it costs anything permanent.

**Before analysis:** run `scripts/audit.py` over every supplied file. Produce the Data Integrity Log covering duplicate IDs, index-vs-catalogue offsets, dummy species slots, orphaned learnset and evolution references, stats outside 1–255, BSTs that do not equal the sum of their parts, and evolution targets that do not resolve. Ship the log even if empty.

**Gate:** row count · stat-order verification recorded · **starter count against `starter_count`** · species with zero level-up moves · unresolved evolution targets · species with no availability record · dummy-slot count with each named.

---

## Phase 2 — World, items, and interactions

**Deliverable: `02_world.tsv`.** One row per acquirable thing or interaction.

The `areas` array is the spine here: 221 entries, each with a name and a set of typed keys. The key vocabulary observed at v4.1 is:

| Family | Keys |
|---|---|
| Wild | `wild-day`, `wild-night`, `wild-surf`, `wild-oldRod`, `wild-goodRod`, `wild-superRod`, `wild-smash` |
| Items | `item-standard`, `item-hidden`, `item-shop`, `item-cheat` |
| Fixed | `fixed-gift`, `fixed-trade`, `fixed-overworld`, `fixed-roaming` |
| Other | `tutors`, `trainers`, `raid1`, `raid3`, `raid4`, `raid5`, `raid6` |

**The inner numeric keys under each of these are not yet identified.** They may be slot indices, rate buckets, sub-area identifiers, or something else. Resolve them from the dex tool's own display and filter code before publishing a single encounter rate — a misread rate is worse than an absent one, because it looks like data. Until resolved, encode rates as `UNK` rather than guessing, and say so at the gate.

Note that `raid2` is absent while `raid1` and `raid3`–`raid6` are present. Determine whether 2-star dens genuinely do not exist in this build or whether the key is named differently, and log the answer either way.

**Mode conditionality is a first-class field here.** A material share of items, TMs and tutors are present in one difficulty mode and absent or substituted in another. The documentation set marks these explicitly and is the better source for the conditionality itself; the extracted database is the better source for the placement. Carry an explicit `mode_availability` column. Only the canonical mode gates the published scores, but the cross-mode difference is retained.

Required columns: entity type · entity name · internal ID · location and region · acquisition method · cost and currency · **quantity, literal** · prerequisites · **`earliest_gate`** · `mode_availability` · trade details · vendor stock · missable flag and reason · source record, confidence tier, notes.

**Gate:** row count by entity type · items with no location · evolution items referenced by Phase 1 that don't appear here · rows where `earliest_gate` is `UNK` · rows where an encounter rate is `UNK` · count of mode-conditional entities · the availability integrity checks G1–G4 from `integrity-checks.md`.

---

## Phase 3 — Trainers, bosses, and the checkpoint graph

**Deliverable: `03_trainers.tsv`.** One row per trainer, roster folded into encoded columns.

Three traps here, all confirmed present in the source, all of which produce plausible-looking wrong answers rather than errors:

**1. Two roster sets per trainer.** Every trainer carries both a default and a hardcore roster. **214 of the 464 differ** — species, levels, items and moves all vary. Parse both, tag each with its mode, and score only the canonical mode. A parser that reads whichever key it finds first will silently mix modes across the dataset.

**2. Cap-relative level sentinels.** Levels in the range 101–104 are **not levels**. They are offsets from the checkpoint cap, resolved through the `scaledLevels` map (103 → +0, 102 → −1, 101 → −2, 104 → −3). **140 of the 464 trainers use them.** Resolve every one against its trainer's `cap` index, store the resolved level and the raw sentinel in separate columns, and flag the trainer as level-scaled. Per §0, scaled trainers are parsed and retained but **never scored** — a roster that rescales to the player is not a fixed target, and including it would distort every ladder it touched.

**3. Boss names are not unique.** Gym leaders appear multiple times as first fights and later rematches. The first Brock and the rematch Brock share a name, sit at different caps, and have entirely different rosters — four Pokémon in the low teens versus six scaled Pokémon including Great Tusk and Tyranitar. **Key bosses on (cap, area, name), never on name.** Report the full list of duplicate names at the gate.

Required columns: trainer ID, name, class, role, location, battle order index, **mode** · level cap in effect · **roster** encoded per slot (species form, resolved level, raw level sentinel, ability, held item, nature, IVs, EVs, all four moves) with the encoding documented precisely · **derived team analysis** (offensive coverage, defensive profile, aggregate speed tier, slowest and fastest members, shared weaknesses, types the team cannot hit for neutral damage, any single type that resists the whole team) · **strategy notes** (prose, `Inferred`): what the team is trying to do, its win condition, its most dangerous member and why, the specific move that most often ends runs, the exploitable seam. Be concrete.

**Also build the checkpoint graph here.** The source hands it over almost complete: 18 named caps in progression order, each with an ID that trainers reference. That ordering is the checkpoint spine — Brock, Archer-1, Misty, Surge, Erika, Giovanni-1, Archer-2, Giovanni-2, Sabrina, Koga, May, Blaine, Archer-3, Giovanni-3, Clair, Brendan, Elite-4, Post-Game. Resolve the two-value cap question from §0 **before** using any of them. Checkpoints without a roster of their own are scored against the roster of the next boss ahead.

**Also write the portability report** at this gate: what, if anything, had to change outside `targets/cinder/`, and for each change, whether it is a genuine core improvement or an adapter that wasn't written properly.

**Gate:** trainer count by mode · roster slot count · unresolved roster references against Phases 1–2 · scaled-level count with all resolved · duplicate-name list · checkpoint count with caps · boss level curve in order, with any non-monotonic stretch flagged as a finding rather than smoothed · portability report.

---

## Phase 4 — Build generation and the 1v1 matrix

**Deliverable: `04_matchups.tsv`**, partitioned per checkpoint.

Generate builds **from each species-form's own profile**, never by applying a template across a role. Move slots fill from the pool **available at that checkpoint**. Build the **entire held-item catalogue**, not a curated subset. Record the pruning rules applied; they are what makes I6 a real test.

**Assign tracks before generating anything** (`VISION.md` §4.3). Physical when `Atk ≥ 1.15 × SpA` and the best available physical move is ≥ 60 BP; special on the mirror condition; mixed when the two stats are within 15% and both pools reach 60 BP; support when the form has whitelisted utility *and* either `max(Atk, SpA) < 80` or neither pool reaches 60 BP. A form may take several tracks. **A form that takes none is a finding** — log the species with its best physical BP, best special BP and max attack stat, and do not drop it silently.

EV spreads are per-track: physical `252 Atk / 252 Spe / 6 HP`, special `252 SpA / 252 Spe / 6 HP`, mixed `252 Atk / 252 SpA / 6 Spe`, support `252 HP / 252 Def / 6 SpD`, floor `no EVs`. **Carry the stat names, not bare numbers** — a spread without the stat it goes into is unusable to a reader.

Item preference is **ranked per track**, not globally. Support ranks longevity, Eviolite, contact punishment and resist berries first; offensive tracks rank Choice items and type boosts first. A single global ranking shifts everyone equally and changes no orderings.

The **support-track utility whitelist is a real gate.** Growl and Tail Whip are status moves and do not make a support Pokémon. Publish the whitelist in `00_README.md` so it can be argued with, and expect to tune it for this target rather than importing SABLE's unchanged.

Compute, for every (build, opposing roster Pokémon) pair at each checkpoint: damage rolls both directions including ability, item, weather/terrain and hazards · speed order including priority and speed modifiers · turns-to-KO both directions and the outcome from full HP · the outcome from a realistic partial-HP state · status and setup interactions where they change the result.

**Store the continuous margin**, and derive the win/loss/marginal verdict from it for display. The margin is what Phase 5 scores. **Utility earns score inside the cell** — hazard chip, status and turn denial, recovery, screens — rather than being added afterwards as a separate adjustment.

**Priority moves must order turns.** SABLE scored priority without simulating it — priority gated the revenge killer and priority abuser roles and fed the tool term while the matrix sorted on raw Speed alone, so 655 published ceilings earned credit for striking first without doing so. Do not repeat that. Every move record in this source carries a `priority` field; use it. If priority genuinely cannot be modelled, stop and say so, then record the affected ceiling count as a stated limit in `00_README.md` and in the app's limits section. The one outcome that is not acceptable is priority silently earning role credit again.

**Store turns-to-KO both directions, raw incoming damage, and incoming after utility, as separate columns.** The sustain axis in Phase 5 reads these cells directly rather than recomputing them, so they are load-bearing outputs of this phase and not diagnostics.

Note the scale before starting: roughly 1,340 species-forms against 18 checkpoints against the authored roster set is a large matrix. Partition, checkpoint at intervals, and report timing at the gate so the cost is visible rather than discovered.

**Gate:** build count and cell count · pruning rules stated · **hand-reproduce at least ten calcs** spanning different types, levels and abilities, and report the discrepancy rate — this is also the confirmation of `mechanics_gen`, which cannot be signed off without it · count of species/moves/abilities/items added to the custom data layer, and count flagged as unsupported.

---

## Phase 5 — Valuation

**Deliverable: `05_valuation.tsv`.** The critical phase. Re-read `roles.md` and `builds.md` first. **Prompt before setting role weights, tier thresholds, or the dead-weight penalty.**

**Roles.** Score within roles, never on one global list. **Gates before scores.** Gates evaluate against moves and abilities available *at that checkpoint*. `role_fit = w_stat·S + w_tool·T + w_type·Y + w_fight·F`, all four components reported. Report the top three role fits per species-form; mark near-ties as hybrids. Species-forms failing every gate are a finding — do not invent a "generalist" bucket.

**Floor and ceiling.** Floor is the zero-investment build. Ceiling is optimal nature, EVs, ability, item and moves **gated by what Phase 2 says is obtainable by that checkpoint**. Store the ceiling's exact build. **The ladder sorts on the ceiling**; the floor is published alongside so the gap is visible.

**ROI** is the strength gained by investing into the best build — the distance from raw to perfected, reported with its cost, not collapsed into a ratio.

**Scarcity gate.** An item counts toward a headline score only if reliably obtainable — purchasable, or three or more copies. Publish **item dependence** per build.

**Replacement baseline.** Third-best obtainable species-form for that (checkpoint, role) under zero investment. **Percentile-normalize within the obtainable pool at each checkpoint.**

**Lineage credit.** Determine which form the line is realistically in at each checkpoint, score that form, aggregate with an explicit **dead-weight penalty**. Store the per-checkpoint form, the raw score, and the penalty separately.

**Sustain axis.** Published alongside role fit, not folded into it (`VISION.md` §4.5a). Walk each boss roster **sequentially on a single lifebar in the order the fight presents it**, accumulating damage and paying it back by healing per turn; **reset the bar at every trainer boundary**. Depth reached before fainting is the raw measure. **Publish the kit delta** — the build minus the same species-form with no kit — because raw depth correlates with BST at r ≈ 0.81 and otherwise measures size rather than kit. Heal per turn as a fraction of max HP: reliable recovery 0.25, Regenerator 0.11, Leftovers-class 0.0625; re-derive these if this target's recovery moves or items differ materially from SABLE's. **Read turns-to-KO and incoming damage off the Phase 4 cells** — do not recompute them, or there are two implementations of one quantity to keep in sync.

**Team layer.** Beam search over teams of six from the checkpoint's pool. **Teams must be simultaneously equippable** given copy counts.

**Output:** final value per species-form and per lineage · tier (S+/S/A/B/C/D/F) with thresholds stated numerically and the distribution reported — do not force a curve · sustain axis · `cant_miss` flag with its rule written down · per-checkpoint score columns retained · confidence tier and reasoning trace per score.

**Also compute what SABLE deferred** (`VISION.md` §12a): `investment_cost` and ROI, and lineage value with its dead-weight penalty. Both shipped as em dashes on SABLE. If either is going to be skipped again, decide that here and say so at the gate — not at Phase 7 when the app has empty columns.

**Gate — a failing invariant blocks the export until it is fixed or explicitly overridden in writing.** An override names the invariant, the observed value, why the failure is acceptable, and what would fix it, and it goes into `00_README.md` and the app's limits section. SABLE shipped with four of seven failing and the rule unchanged on paper; do not repeat that.

Report I3 as the **mean |r| within (checkpoint, role)** — not a global correlation, which is a different and more flattering number — **and name the worst cells with their n**. SABLE's 0.502 mean concealed individual cells at r ≈ 0.93. For reference only, SABLE's shipped results were I1 0.2772 (fail), I2 0.281 (fail), I3 0.502 (pass), I4 117 failing cells, I5 one conflict, I6 0.856 (pass), I7 0.129 (pass). **Those are facts about that hack, not expectations for this one.** If I4 fails broadly on a pool of ~1,340 forms, suspect the role gates before suspecting the pool, and name failing cells individually rather than reporting a count.

---

## Phase 6 — Evaluation

No new dataset. Re-read everything from disk and try to break it.

- **Round-trip** every TSV
- **Cross-phase referential integrity:** every Phase 3 roster species, move, ability and item resolves against Phases 1–2; every Phase 5 ceiling build uses only items and TMs Phase 2 confirms obtainable by that checkpoint **in the canonical mode**
- **Invariant I6:** perturb base stats by ±15 and re-run build generation on a stratified sample of ~150 species-forms, seed recorded. Require the recommended build to change for ≥20%
- **Recompute** the BST correlation and the tier distribution
- **Missing-data sweep:** every `UNK` by column, with a judgment on whether it is recoverable from supplied data or needs something not yet provided. Encounter rates and the caps question are the two most likely residents of this list
- **Sensitivity pass:** the assumptions that, if wrong, would most change the rankings, and the specific species whose tier depends on each. For CINDER the leading candidates are `mechanics_gen`, the caps interpretation, and the encounter-rate encoding. This is the most useful thing Phase 6 produces
- **Consolidated Data Integrity Log** folded into `00_README.md`
- **Final portability report:** total edits outside `targets/cinder/`, each classified

---

## Phase 7 — Companion app

Read `/mnt/skills/public/frontend-design/SKILL.md` first. Single self-contained HTML file in `<output_dir>`, data embedded, opening offline with no build step and no CDN dependency. No `localStorage` or `sessionStorage` — hold state in memory.

The app carries the **Glance** and **Working** depths; Audit lives in `00_README.md`.

- **Glance tab.** One screen for the current checkpoint: a verdict, the two or three team slots most likely to fail at the next boss, and what to do about them. It must commit. Readable on a phone.
- **Dex tab.** Searchable, filterable grid — type, tier, role, availability, checkpoint, can't-miss.
- **Species card.** Everything about one form on one card: stats with bars, typing with the real matchup chart, abilities, complete movepools grouped by source, availability with locations and levels, evolution method and requirements, and the full Phase 5 analysis. **Lineage navigation** both directions.
- **Rankings tab.** Full ordered list with tier bands, filterable by role and checkpoint, with thresholds and the replacement baseline stated on the page.
- **Routes tab.** The progression graph as a route list with its priority grade and stated reason, encounter tables with slot rates and each species' current and projected role rank, catch priority with a one-line reason each, items and TMs flagged with which build they unlock, an explicit missable list with the gate after which each is lost, and a "safe to skip" verdict where honest. **Read-only** — no check-off, no run state.
- **Starters tab.** The 27 Oak's Lab options ranked against each other for the decision actually being made: which one to open the run with. This is **not a filter on the Rankings tab**, because every other view scores a species at a checkpoint and this is a single irreversible choice made at gate 0 that has to pay off across all eighteen. Rank on the **lineage-adjusted score aggregated over the full run**, not the base form's score at gate 0 — you are choosing Venusaur, not Bulbasaur, and the dead-weight penalty for the checkpoints spent as Bulbasaur is exactly what distinguishes the options. Per starter show: the aggregate rank and tier · the per-checkpoint value curve, so a slow starter that peaks at Koga is visibly different from a fast one that fades · **the early window (gates 0–2) called out separately**, because that is when the starter is most of the team and a bad opening is felt hardest · the checkpoint where it comes online, meaning the evolution or move that changes its tier, with the level or item required · the bosses it beats and loses to · its coverage overlap with what the first three routes actually offer, since a starter that duplicates the early wild pool is worth less than its own score suggests. Lead the tab with a committed recommendation and a one-line reason, then the table.
- **State the reversibility, prominently.** All 27 starters reappear in the Celadon shard-trade pool at gate 3. The starter choice is a head start, not a lock, and a tab that implies otherwise is answering a harder question than the one that exists. Say what the choice actually costs: three gates of exclusivity.
- **Dependency:** this tab reads lineage value and the dead-weight penalty (`VISION.md` §12a). Both went uncomputed on SABLE. If they are skipped again, this tab cannot be built honestly — say so at the Phase 5 gate rather than shipping a starter ranking that is secretly a gate-0 base-form ranking.
- **Analysis tabs.** Performance by checkpoint, floor vs ceiling, ROI leaderboard, role leaderboards, a boss matchup explorer, coverage-gap analysis for a proposed party.
- **Markers.** Numeric value and tier badge on every card; can't-miss markers visible in the grid, not only on the detail view.

**House style:** dark green ground, cream paper text, brass and verdigris accents, serif display over sans body, masthead with search, sticky tab nav, sprite cards. Sprites are available as base64 data URIs in the source, so cards can be populated without shipping image files.

Every number carries its confidence tier. A number without one is a bug. This is a reference tool used mid-playthrough on a second monitor: information density and speed matter more than decoration.

---

## What to confirm before Phase 1

§0 is filled. The two provisional entries — `mechanics_gen` and the caps two-value question — are tracked above with the phase each blocks. Everything else in `VISION.md` §12 is answered. Begin at Phase 1 with the stat-order verification.
