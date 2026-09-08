# HALYARD — Vision Document

**Status:** Draft v3 (Target 02 adoption: CINDER) · **Classification:** EXTERNAL (ships to repo root as `VISION.md`)
**Date:** 2026-09-07
**Supersedes:** Draft v2 (single-target, SABLE)

---

## 0. The one-paragraph version

HALYARD is a companion system for playing difficulty-modified Pokémon ROM hacks. Its job is to answer, at any point in a playthrough: *what should I be catching, what should I be building, and what am I about to miss?* It answers those questions from the hack's own data rather than from community consensus or from what a language model remembers about Pokémon. Underneath, it computes an exhaustive 1v1 matchup matrix; on the surface, it publishes replacement-relative value with a floor, a ceiling, and the cost of getting from one to the other. Target 01 (**SABLE**) was a Hoenn-based hack built on `pokeemerald-expansion`, ingested from a decompilation. Target 02 (**CINDER**) is a Kanto-based hack with no public decompilation, ingested instead from an extracted runtime database. That difference is the point: the adapter absorbs it and the engine does not change.

---

## 1. Codename and naming policy

| Layer | Codename | Meaning |
|---|---|---|
| Framework | **HALYARD** | The reusable engine, skill, and presentation layer |
| Target 01 | **SABLE** | Hoenn-based, `pokeemerald-expansion` decomp source |
| Target 02 | **CINDER** | Kanto-based, extracted-database source — the current work |
| Future targets | MARROW, … | One codename per hack, assigned on adoption |

**Repository name:** `halyard`

**Naming rules, binding on all EXTERNAL artifacts:**

1. No franchise-identifying words in the repo name, repo description, topics, README title, or commit messages.
2. The repo description is generic: *"A data-driven planning framework for turn-based RPG progression."*
3. Target folders use codenames (`targets/cinder/`), never the hack's public name.
4. Species names, move names and map names inevitably appear **inside data files** — unavoidable and acceptable. The goal is that the repo is not findable by someone searching for the hack, not that the contents are obfuscated.
5. No topics or tags on the GitHub repo. No links to it from any forum, Discord, or wiki.
6. Never commit ROM files, save files, or game assets. Derived numeric tables only.

**The seams.** Two, now, rather than one:

- The working prompt (`RUNBOOK.md`) is a template and is EXTERNAL. Its **target configuration block**, which names the hack in plain language, is INTERNAL and is never committed.
- The **target adapter skill** for CINDER names the target's source file layout, and a source layout is identifying in a way a species list is not. It is therefore classified **INTERNAL**, unlike the core `halyard` skill. See §9.

**A known leak, named rather than papered over.** The damage engine (§4.2) is a public fork whose repository name identifies the target. Any EXTERNAL artifact citing that dependency by URL identifies CINDER to a reader who is looking. Three options, none free: pin the dependency by commit hash without the owner name; vendor the needed mechanics files; or accept the leak on the grounds that a dependency URL is not a search term anyone would use to find this repo. **Currently accepting**, and recording it here so the decision is deliberate rather than an oversight.

---

## 2. What this is, and what it is not

**It is:**
- A planning and analysis tool for a single human playthrough.
- A framework whose value compounds — each target adopted should be cheaper than the last.
- Opinionated. It makes recommendations and states its reasoning.

**It is not:**
- A wiki, a walkthrough, or a replacement for playing the game.
- A battle simulator. Damage math is a component, not the product.
- A general-audience app. It is built for one player's workflow; if others find it useful, fine.
- Live-connected to a running game. No ROM reading, no save-state parsing, no emulator hooks.

---

## 3. Success criteria

HALYARD succeeds on CINDER if all of these hold:

1. **Pre-boss usefulness.** Before each major fight, the system names the two or three team slots most likely to fail and what to do about them, and is right more often than a coin flip.
2. **No blind misses.** Nothing one-time and high-value is missed because the system failed to flag it before the point of no return.
3. **Recommendation diversity.** Recommended builds across a full playthrough are not dominated by one item, one nature, or one move. See the invariants in §4.9.
4. **Traceability.** Any recommendation can be drilled into, down to the source record it derives from.
5. **No silent loss.** Every field present in the source is present in the dataset, every excluded row is named in the Integrity Log with its reason, and every gap is encoded rather than omitted.
6. **Portability, demonstrated rather than asserted.** CINDER is onboarded with **zero edits outside `targets/cinder/`**. This is now a live test rather than a promise, and it is a hard one: SABLE was a C decompilation and CINDER is a JavaScript object literal, so any hidden decomp assumption in `core/` will surface here. Finding those is a deliverable.

---

## 4. Pillar I — The ranking system

Unchanged from v2 in structure. Only the clauses that CINDER materially changes are restated in full below; everything else is inherited.

### 4.1 The unit being ranked

The atom is **(species-form, build, checkpoint)**, where *build* = (ability, nature, held item, four moves, EV/level assumption) and *checkpoint* = a named progression gate.

**Species-form, not species.** Regional variants, mega forms, and hack-specific forms each get their own row and their own builds, linked by a shared lineage key. CINDER's source supplies that lineage key directly as an `ancestor` field, and it supplies a separate catalogue number (`dexID`) alongside the internal index (`ID`) — carry both, per §7.

A "rank" surfaced to the player is always a projection of this atom — most often *"best build of species X, at checkpoint M."* Say which projection is being shown.

### 4.2 The primitive: 1v1, exhaustively computed

**The 1v1 matchup matrix is the primitive. Everything the player sees is derived from it.**

Rationale: 1v1 outcomes are exhaustively computable — every candidate build against every Pokémon on every boss roster. Team evaluation is combinatorially explosive and cannot be exhaustive. Building teams on top of a complete 1v1 matrix gives both, and keeps the expensive layer honest because it rests on measured numbers.

For each (build, opposing Pokémon) pair, compute damage rolls both directions including ability, item, weather/terrain and hazard effects; speed order including priority and speed modifiers; turns-to-KO both directions and therefore the outcome from full HP; the outcome from a realistic partial-HP state; and status and setup interactions where they change the result. Output a **continuous margin**, from which a win/loss/marginal verdict is derived for display — the margin is what gets stored and scored, never the discretized verdict alone.

**The engine.** A fork of `@smogon/calc` (v0.9.0, MIT), used through the `adaptable` entry point with a **custom data layer built from the Phase 1 species table**. The calculator supplies *mechanics*, never *data*. Its bundled data layer is never used, and any species, move, ability or item present in the target but absent from the calculator is added to the custom layer or flagged — never silently substituted.

Two consequences, stated once and inherited everywhere:

- The generation whose mechanics the target uses is **pinned and named in the README**. Every cell inherits that assumption.
- A matrix cell is therefore **Derived**, not Measured, however solid its inputs. Only a figure confirmed in-game is Measured.
- Every calc is stored with its full input set — both Pokémon's level, nature, EVs, IVs, ability, item, boosts, field state, and move. A damage range without its inputs is not evidence.

**One inherited defect, named so it gets fixed rather than re-shipped.** In SABLE, **move priority was scored but did not move first**: it gated the revenge killer and priority abuser roles and fed the tool term, while the matrix ordered turns on raw Speed alone. 655 published ceilings carried a damaging priority move that never actually struck first. That is a role score resting on a mechanic the engine did not simulate, which is precisely the seam this framework exists to keep visible.

**For CINDER, priority is modelled in speed order.** The calculator supports it, the data carries a `priority` field on every move, and a target of this size will have a proportionally larger number of affected cells. If it turns out to be infeasible, it is recorded in this section as a known limit with the affected ceiling count — the one thing it may not do is silently earn role credit again.

### 4.3 Build generation, and how the explosion is contained

Builds are generated **from the species-form's own profile**, never by applying a template across a role. Move slots are filled from the pool **available at that checkpoint**, not the lifetime pool.

**Four tracks, assigned by the profile, not chosen.** A species-form qualifies for one or more tracks and gets builds only on the tracks it qualifies for. The thresholds below are SABLE's, carried forward as the starting point; they are target-tunable but they are not target-optional, because the track assignment is what makes I6 a real test rather than a formality.

| Track | Qualifies when | EV spread | Damaging moves |
|---|---|---|---|
| **Physical** | `Atk ≥ 1.15 × SpA` and the best physical move available is ≥ 60 BP | 252 Atk / 252 Spe / 6 HP | 3 |
| **Special** | `SpA ≥ 1.15 × Atk` and the best special move available is ≥ 60 BP | 252 SpA / 252 Spe / 6 HP | 3 |
| **Mixed** | The two attack stats are within 15% of each other *and* both pools reach 60 BP | 252 Atk / 252 SpA / 6 Spe | 4 |
| **Support** | The form has real utility moves *and* (`max(Atk, SpA) < 80` **or** neither move pool reaches 60 BP) | 252 HP / 252 Def / 6 SpD | 0–2 |

**The support track is a first-class measured track, not a consolation prize.** A species-form with no viable attacking track is not dropped from the analysis; it is scored on what it actually does. Two constraints keep the track honest:

- **Real utility gates.** The utility that qualifies a form for the support track is drawn from an explicit whitelist of moves that change a fight. Growl and Tail Whip do not make a support Pokémon, and a track that accepted them would fill with chaff and drown the forms that genuinely belong there.
- **Its own item preference ordering.** Support builds rank longevity, Eviolite, contact punishment and resist berries at the top, where an offensive track ranks Choice items and type boosts. A single global item ranking applied across tracks shifts everyone equally, changes no orderings, and is theatre.

A form may qualify for several tracks and gets builds on each. A form that qualifies for none is a **finding** — record it with the reason (best physical BP, best special BP, max attack stat) rather than silently dropping it.

The full enumerated set is retained internally; what is *published* per (species-form, checkpoint) are the two anchor builds of §4.4.

### 4.4 What the player sees: floor, ceiling, ROI, and VORP

- **Floor** — the zero-investment build: neutral nature, 0 EVs, 31 IVs, the more common ability, no held item, level-up moves only.
- **Ceiling** — best nature, EV spread, ability, held item and moves, **gated by what Phase 2 confirms is obtainable by that checkpoint.** A ceiling resting on an item the player cannot hold for two more badges is a fiction; cap it at what is reachable and name the gate.
- **`investment_cost`** — a documented composite of what the ceiling requires: an egg move or hidden ability, EV training time, a contested TM, a one-of-a-kind item, a specific nature, an evolution item.
- **ROI** — the strength gained by investing into a species-form's best build: the distance from raw to perfected, reported alongside the cost, not collapsed into a gain-per-cost ratio.
- The ceiling's exact build is stored, so it can be reproduced and argued with.

**Rankings present the perfected build.** A species-form is rated on what it becomes when built properly, not discounted for what is unreachable in the first two hours. The floor is published alongside so the reader can see the gap; it is not what the ladder sorts on.

**Replacement baseline.** For a given (checkpoint, role) cell, replacement level is the performance of the **third-best obtainable species-form for that role at that checkpoint under zero investment.** **Percentile-normalize within the obtainable pool at each checkpoint**, never min-max across the whole dex, or legendaries flatten everyone else.

### 4.5 Roles, not one ladder

Every build is scored against a fixed set of roles and rankings are published per role; the taxonomy lives in the skill's `references/roles.md`. Three rules govern scoring:

**Gates before scores.** Every role has binary requirements. Fail one and the build is disqualified regardless of stats — a wall without recovery is not a wall. Gates evaluate against the moves and abilities **available at that checkpoint**, not the lifetime pool.

**Fight fit.** `role_fit = w_stat·S + w_tool·T + w_type·Y + w_fight·F`, weights summing to 1, all four components reported alongside the total. `F` is the boss-relative term and is what distinguishes this from a generic tier list.

**Report the top three, not the winner.** Emit a ranked list of role fits; name the top one `primary_role`, and where the runner-up is within ~0.05, mark it a hybrid and name both. Species-forms that fail every gate are a finding, not a bug. Do not invent a "generalist" bucket to absorb them.

**Utility scores inside the 1v1 primitive.** Hazard chip, status and turn denial, recovery, and screens earn score within the matchup cell rather than being bolted on afterwards as a separate adjustment.

### 4.5a The sustain axis

Role fit measures whether a build can do a job. Sustain measures **how long it stays on the field while doing it**, and it is published as its own axis rather than folded into a role score.

The naive construction fails, and the failure is worth stating because it is the reason the axis looks the way it does. Scored per opposing slot, sustain saturates: almost everything survives one individual Pokémon, so a wall and a glass cannon both land at 0.82–0.99 and the axis discriminates nothing. Scored across a whole checkpoint on one continuous lifebar, it collapses the other way: everything scores 1–3.

The construction that works:

- **Walk the roster sequentially on a single lifebar.** Damage accumulates across slots; healing pays it back per turn. How deep a build gets before fainting is what separates a wall from an attacker that survives one hit.
- **Reset the bar at every trainer boundary**, because the player heals between fights. Carrying damage across a whole checkpoint is what produced the 1–3 collapse.
- **Use roster order as the fight presents it.** Sorting hardest-first is a worst-case ordering that zeroes genuine walls on their opening slot, and the player does not choose to lead into the ace.
- **Publish the kit delta** — this build minus the identical species-form with no kit — because raw depth correlates with BST at r ≈ 0.81 and therefore measures size rather than kit. The delta is the part that is about the build.

Healing is modelled per turn as a fraction of max HP: reliable recovery ≈ 0.25 (it restores more, but it costs the turn), Regenerator ≈ 0.11 (a third of max HP per switch, amortised), Leftovers-class passive ≈ 0.0625. These constants are inherited from SABLE and should be re-derived rather than assumed if CINDER's recovery moves or item set differ materially.

**Turns-to-KO and incoming damage are read off the matchup matrix**, not recomputed. The matrix already stores turns-to-KO both directions, raw incoming, and incoming after utility. A second, independent implementation of the same quantity is a second thing to keep in sync and a second place to be wrong.

### 4.6 Lineage: scored forward, with a dead-weight penalty

For each checkpoint, determine which form the lineage is realistically in at that point given its evolution method and gate, and score **that form**. The lineage-adjusted score is the checkpoint-weighted aggregate across the line, with an explicit **dead-weight penalty** for checkpoints where the line is stuck in an underperforming form. Store the per-checkpoint form used, the raw score, and the penalty separately. A weak species that becomes a top-3 answer two checkpoints later is flagged as an **investment**, with the payoff checkpoint and the cost stated.

### 4.7 Team layer

Team value is a **marginal contribution** measure, computed by beam search over teams of six drawn from the checkpoint's available pool. A team's fit against a boss is coverage of that boss's threat set, weighted by how badly each unanswered threat loses the fight; a build's team score is how often it appears in the top-N teams and how much the best team degrades when it is removed. **Team recommendations must be simultaneously feasible** — two members cannot both hold the game's single Choice Scarf.

### 4.8 Inputs to a build's score

Base stats drive which builds are generated at all. Typing drives offensive coverage and the defensive matchup against the specific boss roster. Ability is enumerated per slot and is part of the build, never averaged. Level-up moves are gated by the level the species is at that checkpoint; TM moves by whether that TM is obtainable by then and by copy count; egg and tutor moves by whether the parent chain or tutor is obtainable. Nature is enumerated and scored, not assumed. Held items are gated per species by whether it can exploit the item, and by scarcity.

**Scarcity gate.** An item only counts toward a build's headline score if it is *reliably obtainable* — purchasable, or present in at least three copies. The gap between "best item overall" and "best reliably-obtainable item" is published as **item dependence**, per build.

**The whole held-item catalogue is built**, not a curated subset. Curation is where an analyst's priors leak into what is supposed to be a measurement.

### 4.9 The anti-degeneracy invariants

| # | Invariant | Threshold | Checked at |
|---|---|---|---|
| I1 | No single held item in more than 25% of recommended builds | ≤ 0.25 | Phase 5 |
| I2 | No single nature in more than 20% of recommended builds | ≤ 0.20 | Phase 5 |
| I3 | Correlation between final rank score and BST | \|r\| ≤ 0.60 | Phase 5 |
| I4 | Every role at every checkpoint has ≥ 3 species-forms within 10% of the leader | ≥ 3 | Phase 5 |
| I5 | Recommended teams are simultaneously equippable given copy counts | 100% | Phase 5 |
| I6 | Perturbing base stats by ±15 changes the recommended build for ≥ 20% of species | ≥ 0.20 | Phase 6 |
| I7 | No move in more than 30% of recommended movesets (obligatory STAB fillers excluded and reported separately) | ≤ 0.30 | Phase 5 |

**I3 is a mean of within-cell correlations, not a global one.** The statistic is `mean |r| between VORP and BST computed within each (checkpoint, role) cell`, not a single correlation across the whole table. These are different numbers and the distinction is not cosmetic — a global correlation is dominated by cross-role variance and will read low while individual cells are near-perfect BST sorts. Report the mean, **and report the worst cells with their n**, because that is where the model is actually failing. SABLE's pass hid cells at r ≈ 0.93 behind a mean of 0.502.

I3 has a floor as well as a ceiling: near-1.0 means the model is an expensive way to sort by BST; below about 0.25 it is probably broken in the other direction, and that is **reported, not blocked**.

**Do not import SABLE's numbers as CINDER's expectations.** For the record, SABLE's shipped Phase 5 landed at I3 = 0.502 (pass), I6 = 0.856 (pass), I7 = 0.129 (pass), I1 = 0.2772 (fail, Berry Juice), I2 = 0.281 (fail, Calm), I4 = 117 failing cells, I5 = one item-copy conflict. Those are a fact about that hack and that weight set, not a prior for this one.

**On "all seven block release."** The v2 rule was that a failure stops the export. SABLE then shipped with four of seven failing. A rule that is overridden in practice and unchanged on paper is worse than no rule, because it stops carrying information. The rule for CINDER is therefore:

> **A failing invariant blocks release until it is either fixed or explicitly overridden in writing.** An override names the invariant, the observed value, the reason the failure is judged acceptable, and what it would take to fix — and it appears in `00_README.md` and in the app's own limits section, not only in a gate log.

This keeps the invariants load-bearing while making the escape hatch visible. "I1 fails at 0.2772 because Berry Juice is the only reliable longevity item before the fourth gate, and the fix is a wider early item pool" is a finding. Silently shipping is not.

**I4 has more room to breathe on CINDER.** The available pool is roughly 1,340 species-forms rather than a few hundred, and SABLE's 117 failing cells were judged "mostly genuine role scarcity." At CINDER's pool size that defence is much weaker: if I4 fails broadly here, suspect the role gates before concluding the hack is thin. Cells that genuinely lack three viable options should be named individually, not aggregated into a count.

**I6 runs on a stratified sample of ~150 species-forms, once, at Phase 6**, stratified across BST quartiles and evolution stages, with the sample and seed recorded.

### 4.10 Availability gating

Every score is computed at a checkpoint, with the level cap applied (read from source, never assumed), TM/HM availability derived from actual placement, literal item copy counts, species availability across all channels, and evolution feasibility.

**CINDER adds a difficulty-mode axis to availability that SABLE did not have.** A meaningful share of items, TMs and tutors in this target are conditional on difficulty mode — present in one mode, absent in another, or swapped for a different item. Availability is therefore a function of (checkpoint, **mode**), and the canonical mode is pinned in the target config. Cross-mode differences are recorded rather than discarded, because they are the cheapest possible answer to "what changes if I switch modes," but only the canonical mode's availability gates the published scores.

### 4.11 Published outputs

Per-role, per-checkpoint ladders · per-species-form dossier (floor, ceiling, ROI, item dependence, investment payoff, per-checkpoint curve, and the boss Pokémon it beats and loses to) · per-boss threat sheet · **a starter ladder**, ranking the game-start options on lineage-adjusted value aggregated across the whole run rather than on their value at the gate where they are chosen · tier assignment (S+/S/A/B/C/D/F) with thresholds stated numerically and the distribution reported — **do not force a curve** · `cant_miss` flag with its rule written down · the full 1v1 matrix as a machine-readable artifact, partitioned per checkpoint where row counts demand it.

**The starter ladder is a distinct published output, not a view.** Every other ranking answers "what is best here, now." The starter question is a single irreversible choice made with no information, before the first gate, that has to survive eighteen checkpoints — so it is scored over the run, and it is the one place where the lineage aggregate and its dead-weight penalty are the headline number rather than a supporting column.

---

## 5. Pillar II — Route and encounter reference

### 5.1 Model

The world is a **progression graph**: maps as nodes, gated by checkpoint. Each node carries encounters with slot rates, ground and hidden items, shop stock, TMs, tutors, trainers, gift and trade Pokémon, static encounters, and raid dens with their star tiers.

### 5.2 Route priority scoring

Each location gets a grade with a stated reason, from four terms: **immediate value** (does anything here improve the team for the next boss), **lineage value** (does anything here evolve into a top answer for a later boss), **scarcity** (is anything here unavailable or much harder to get elsewhere), and **missability** (is anything here permanently lost if I walk past it). Scarcity and missability weigh hardest, because they are the only irreversible ones.

### 5.3 Per-route breakdown

Encounter table with slot rates, level ranges, and each species' current and projected role ranks · a **catch priority** ordering with a one-line reason each · items and TMs flagged with which species they unlock a build for · trainers worth fighting for a specific reason · an explicit **missable list** with the gate after which each is lost · a "safe to skip" verdict where that is the honest answer.

### 5.4 The route view is read-only

It shows what a route holds and what that is worth. It does **not** track caught/obtained/skipped state, and there is no checklist to tick. This is a deliberate scope cut carried over from SABLE: run-state tracking was the feature least used and the one most likely to put personal save data somewhere it shouldn't be. Missability is surfaced as a **property of the route**, prominently, rather than as a task list.

---

## 6. Pillar III — Presentation

Three depths, always all three.

| Depth | Form | Purpose | Test of success |
|---|---|---|---|
| **Glance** | One screen. A verdict and three bullets. | Mid-session, in-game decisions | Readable on a phone between battles |
| **Working** | Sortable tables, workbook, filterable app, charts | Planning between sessions | Every recommendation is comparable against its alternatives |
| **Audit** | Full derivation, source references, integrity log, invariant results | Trusting the above | Any single number traces to the record it came from |

**Depths are layers of the same artifacts, not three separate files.** Working is the companion app plus the xlsx workbook. Audit is the bundle's `00_README.md`. Glance is a tab in the app.

The Glance layer is the one most often skipped and the one actually read most. Write it last, from the finished analysis, and make it commit. "It depends" is not a Glance answer.

Rules: every displayed number carries a confidence tier · charts serve a named decision or they get cut · the app is a single HTML file that opens offline with no build step and no CDN dependency · data ships human-readable and machine-readable · the primary human-readable deliverable for a modelling pass is an **xlsx workbook that shows the work**, with live formulas so a weight can be changed and the ladder watched to move.

**House style.** The companion app carries the established look: dark green ground, cream paper text, brass and verdigris accents, a serif display face over a sans body, masthead with search, sticky tab navigation, sprite cards. CINDER's source ships sprites as base64 data URIs, so the cards can be populated without shipping image assets — which also keeps rule 6 of §1 satisfied, since a data URI derived at parse time is a derived numeric table, not a committed game asset. Confirm that reading before relying on it.

---

## 7. Data discipline

### 7.1 Non-negotiables

1. **Every number is computed, not recalled.** Memory of vanilla base stats, movepools, or type charts is a hypothesis. Load the file, run the code, show the arithmetic.
2. **No information is dropped, ever.** If the source has it, the dataset has it. If a field is empty in the source, encode the sentinel; do not omit the column. If a row is excluded from an aggregate, the Integrity Log names the row and the reason.
3. **Ambiguity gets named, not smoothed.** Two sources disagreeing is a deliverable.
4. **Verify before presenting.** Re-read every file written, confirm row counts round-trip, and decode at least three encoded cells back to something recognizable.

### 7.2 Encoding conventions

| Convention | Format | Example |
|---|---|---|
| List | comma-separated | `4,7,12` |
| Key:value pairs | `key:value`, comma-separated | `33:1,45:3` |
| Grouped records | pipe-separated records, colon-separated fields | `route3:grass:12-14:20:day` |
| Not applicable | `NA` | |
| Empty but valid | `NONE` | |
| Unknown / absent from source | `UNK` | |
| Literal tab, newline or pipe in a value | escaped `\t`, `\n`, `\|` | |

`NA`, `NONE`, and `UNK` mean three different things and must never be collapsed. `NONE` is a measurement. `UNK` is a gap. `NA` is a category error.

### 7.3 Confidence tiers

- **Measured** — parsed directly from source; the file and record can be named
- **Derived** — computed from Measured inputs by a stated formula (this includes every damage calculation)
- **Inferred** — reasoned from context, including interpretive prose such as a boss's win condition
- **Asserted** — taken from a secondary source without source confirmation

There is no `Unresolved` or `Speculative` tier. **Gaps are carried by the `UNK` sentinel and by the Integrity Log**, not by the confidence column — the tier says *how we know*, never *whether we know*.

### 7.4 Source hierarchy — rewritten for CINDER

SABLE's hierarchy assumed a decompilation at priority 1. CINDER has no public decompilation, so the hierarchy inverts around a different primary. This is an adapter-level decision and does not generalize to future targets.

| Priority | Source | Use |
|---|---|---|
| 1 | **The extracted runtime database** shipped with the community dex tool | All numeric data: species, moves, abilities, items, types, encounters, placements, trainer rosters, level caps. This is the closest thing to source that exists for this target |
| 2 | **The official documentation set** (changelog, boss sheets, location and item sheets, egg pools, evolution changes) | Corroboration, progression ordering, prose context, and anything genuinely absent from (1) — notably difficulty-mode conditionality on items and the human-readable names for gates |
| 3 | `@smogon/calc` fork | **Mechanics engine only.** Its bundled data layer is never used |
| 4 | Model knowledge | Hypothesis generation only. Never a value in a shipped artifact |

**(1) wins on numbers; (2) wins on ordering and prose.** Where they disagree on a number, (1) is used and **the disagreement is logged as a finding** — the documentation is hand-maintained and lags the build, so disagreements are expected and are themselves informative about which doc pages are stale.

**The tier consequence.** Data parsed from (1) is `Measured`. A fact taken from (2) without corroboration in (1) is `Asserted`, not `Measured`, however official the sheet looks — it is a secondary source. The changelog in particular describes *intent*, which is a different thing from behaviour, and its claims about what changed are `Asserted` until the data confirms them.

---

## 8. Framework portability

The line between HALYARD and a target is the **adapter**. A new hack is onboarded by supplying:

1. **Source binding** — repo and branch, or a directory of exported data
2. **Parser bindings** — where species, moves, abilities, items, learnsets, encounters, trainers, evolutions and maps live in *that* source's layout
3. **Checkpoint list** — the ordered progression gates and the flag, map or cap that gates each
4. **Boss roster mapping** — which trainer entries count as bosses at which checkpoint
5. **Mechanics config** — generation-dependent switches
6. **House rules** — the player's own run constraints, including difficulty mode where the target has one

Everything else — build generation, matchup computation, role scoring, valuation, team search, invariant checks, exports, the app — is target-agnostic and lives in the core.

**Portability test:** onboarding CINDER must require zero edits to files outside `targets/`. Any edit forced outside `targets/` is logged with the reason, and is either a genuine core improvement or an adapter that hasn't been written properly. Say which.

**Two things CINDER is expected to expose in the core**, both worth fixing rather than working around:

- **The mode axis.** SABLE had one roster set; CINDER has two, and `core/` currently assumes a trainer has *a* roster. Mode belongs in the core as a first-class dimension with a single-value default, not as a CINDER-specific hack.
- **Cap-relative levels.** SABLE's trainers had literal levels. CINDER encodes some levels as offsets from the checkpoint cap, resolved at parse time. Level resolution therefore belongs behind an adapter hook, not inlined in the parser.

**Checkpoints are any progression gate, not only bosses.** Gates without a roster of their own are **scored against the roster of the next boss ahead of them**.

---

## 9. INTERNAL vs EXTERNAL

Classify at creation, not at publication.

**INTERNAL — local disk only.** Raw source dumps and extracted databases; snapshots of documentation sets; intermediate parse artifacts; weight-tuning worksheets and calibration notes; personal run state; the filled target configuration block; **the CINDER target adapter skill**; anything that only makes sense with the target's source present.
Naming: `INT_<topic>_<version>.<ext>`.

**EXTERNAL — ships to the repo.** The engine, parsers, adapters, and the core analysis skill; processed self-describing datasets; the rendered app; documentation including this file and the `RUNBOOK.md` template; integrity logs and invariant reports.
Naming: `EXT_<topic>_<version>.<ext>`, or conventional repo names.

**The test:** can this artifact be used by someone who doesn't have the source? If yes, EXTERNAL.

**Two deliberate exceptions, both recorded rather than assumed:**

- Parsers and the engine are EXTERNAL although they consume source. The reusable engine *is* the product, and needing a target to run against is the point.
- The **CINDER adapter skill is INTERNAL**, departing from v2 where "the analysis skill" was blanket EXTERNAL. The core `halyard` skill remains EXTERNAL; the target adapter skill documents a specific source's file names and record layout, which is identifying in a way that a list of species names is not. The over-cautious classification costs nothing and is reversible; the reverse is not.

---

## 10. Repository layout

```
halyard/
├── README.md                  # generic description, no franchise terms
├── VISION.md                  # this document
├── RUNBOOK.md                 # working prompt template, target block empty
├── core/
│   ├── ingest/                # format-agnostic parsers
│   ├── model/                 # build generation, 1v1 matrix, roles, valuation, team search
│   ├── invariants/            # the I1–I7 checks
│   └── export/                # dataset + bundle writers
├── targets/
│   ├── sable/
│   └── cinder/
│       ├── adapter.py         # parser bindings for the extracted-database layout
│       ├── checkpoints.yaml   # the 18 gates, caps, boss mapping
│       ├── mechanics.yaml     # generation config overrides
│       └── modes.yaml         # difficulty-mode axis and canonical selection
├── skill/                     # the core analysis skill (EXTERNAL)
├── datasets/cinder/           # processed EXTERNAL bundle
└── app/                       # single self-contained HTML companion
```

The CINDER adapter skill lives outside this tree, on local disk, per §9.

---

## 11. Phases

Seven phases, each ending in a hard gate. At a gate: present row counts, the Integrity Log, and the validation numbers, then **stop and wait for explicit sign-off.**

| Phase | Deliverable | Gate |
|---|---|---|
| **1** | `01_species.tsv` — species-form master | Row count, index-vs-catalogue offset documented, zero-movepool count, unresolved evolution targets, stat-order verification |
| **2** | `02_world.tsv` — items, TMs, tutors, vendors, trades, encounters, gates | Row count by entity type, items with no location, `earliest_gate` = `UNK` count, mode-conditional item count |
| **3** | `03_trainers.tsv` — trainers, bosses, checkpoint graph | Trainer and slot counts, unresolved roster references, cap-relative levels resolved, boss level curve, duplicate-name disambiguation |
| **4** | `04_matchups.tsv` — build generation + 1v1 matrix | Cell count, calc reproducibility spot-check, unsupported-mechanic count |
| **5** | `05_valuation.tsv` — roles, floor/ceiling/ROI, VORP, teams | I1–I5, I7 pass; tier distribution; BST correlation with n |
| **6** | Evaluation — no new dataset | I6 passes; round-trip; sensitivity pass; consolidated Integrity Log |
| **7** | Companion app | Opens offline; every number traces to a dataset row |

The portability report — what, if anything, had to change outside `targets/cinder/` — is written at the Phase 3 gate, while the memory of the ingest is fresh, and revisited at Phase 6.

---

## 12. Intake status

The v2 intake list, with CINDER's answers.

| # | Item | Status |
|---|---|---|
| 1 | Data files | **Supplied.** Extracted database covering species, moves, abilities, items, types, areas, trainers, caps; plus the official documentation set and the calculator fork's source |
| 2 | Base and mechanics | **Provisional.** Modern mechanics; the exact generation is pinned in the target config and **confirmed by spot-check at Phase 4**, not assumed from the calculator's file layout |
| 3 | Custom content | **Present and material.** The target carries hack-specific forms, moves, abilities and signature items. Every one absent from the calculator's data must be added to the custom layer or flagged |
| 4 | Difficulty mode | **Answered.** Default mode, minimal-grinding off. Roster sets differ between modes for a large share of trainers, so this selection is load-bearing rather than cosmetic |
| 5 | Level caps and obedience | **Supplied by source.** Eighteen named caps form the checkpoint spine. Whether the two values each cap carries are mode variants, pre/post-badge values, or something else is **unresolved and must be settled in Phase 3 before any level is used** |
| 6 | Run rules | Normal play; no nuzlocke, no set-mode constraint, no species clause |
| 7 | Investment tools | Derived from Phase 2 rather than declared — the target's item set is parsed, so vitamins, ability-modifying items, relearner and tutors resolve as ordinary availability |
| 8 | EV/IV assumption | Default: 31 IVs; ceiling EVs optimal, floor EVs zero |
| 9 | Boss set | Trainers with concrete, authored rosters. **Level-scaled trainers are excluded from scoring** — a roster that rescales to the player is not a fixed target and would distort every ladder it appeared in. They are parsed, retained, and flagged, never scored |
| 10 | Legendaries | In-pool but flagged. Availability gating handles most of the distortion |
| 11 | Vanilla dump | Not supplied. Any vanilla baseline is `Inferred` and labeled so |
| 12 | Replacement level | Default: third-best obtainable, zero investment |

---

## 12a. What SABLE specified but never computed

Four things in this document were in SABLE's spec and are absent from its shipped output, rendering as em dashes in the app rather than as numbers. They are listed here so CINDER makes a decision about each at Phase 5 rather than discovering the gap at Phase 7.

| Deferred in SABLE | Status for CINDER |
|---|---|
| `investment_cost` and ROI (§4.4) | **Build.** ROI framed as the strength gained from investing into the best build is a settled decision, and a ranking that sorts on the ceiling without publishing the distance to it is only half the answer |
| Lineage value and the dead-weight penalty (§4.6) | **Build.** CINDER's source supplies `ancestor` and structured evolution methods, so the input side is cheaper here than it was for SABLE |
| Per-checkpoint EV spread | Optional. The per-track spreads in §4.3 cover the common case; revisit only if a checkpoint-specific spread changes an ordering |
| Gift creatures and in-game trades | **Build.** SABLE never parsed them. CINDER's source exposes them directly as `fixed-gift` and `fixed-trade` area keys, so the cost is small and the value is high — gifts are exactly the one-time, high-value entries the `cant_miss` flag exists for |

Two further SABLE limits worth carrying as targets to beat rather than defaults to inherit: 120 of its 127 encounter maps had `Asserted` timing read from a published route order rather than from source, and nine hack-custom boss forms never made it into its species table. CINDER's named cap table and complete species records should let both do better; if they do not, say so explicitly.

---

## 13. Non-goals

- Live game-state integration
- Multiplayer, PvP, or competitive metagame analysis
- A hosted web app or any public deployment
- Breeding/IV optimization tooling
- Speedrun routing
- Run-state tracking or checklists (§5.4)

---

*This document is the reference point for scope disputes. When a proposed feature isn't covered here, either it's out of scope or this document is out of date — resolve which before building it.*
