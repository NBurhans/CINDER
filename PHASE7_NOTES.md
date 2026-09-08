# Phase 7 notes

## Two results that look wrong and probably are not

**The top three at Koga are Floette, Flabébé and Swirlix — all S+, all `cleric`, all
Berry Juice.** That is the utility weighting doing what it was designed to do: with no
stat term, a Fairy with reliable recovery and status scores on tools and fight
relevance rather than on base stats. It is also the case the role taxonomy says the
framework exists to surface. But three near-identical Fairies sweeping a checkpoint is
a thin-cell smell, and Koga is a Poison gym, so Fairy resisting his STAB may be doing
more work than the role model is.

**Froakie tops the starter ladder**, ahead of Sobble and Scorbunny, on lineage-adjusted
value across all eighteen gates with a strong early window. Plausible, and worth
checking against how the run actually plays before trusting it.

Both are checkable against the data in the app, which is the point of building it.

## Interface decisions

The routes view is read-only. Run-state tracking was the feature least used on the
previous target and the one most likely to put personal save data somewhere it should
not be. Missability is shown as a property of the route, in place.

The starters tab is a distinct output rather than a filter on rankings. Every other
view scores a species at a checkpoint; the starter question is one irreversible choice
made at gate 0 with no information that has to survive eighteen checkpoints. It ranks
on the lineage aggregate with its dead-weight penalty, and it states the reversibility
prominently — all 27 reappear in the Celadon shard pool at gate 3, so what the choice
costs is three gates of exclusivity, not a run.

## The species card

The first card shipped a twelve-row definition list and dropped most of what the
pipeline had already computed. It now carries, per selected checkpoint: the stat radar
and bars, the damage-taken chart read from the hack's own matchup arrays, the line with
navigation both ways and structured evolution methods, a ceiling-and-floor curve across
all eighteen checkpoints, the checkpoint block (ceiling, floor, VORP, role, item and its
dependence, track and setup reason, replacement, switch-in survival, team contribution),
the run aggregate with ROI and lineage value against the dead-weight penalty, the sustain
block, every role fit with its S/T/Y/F parts, the ceiling build with nature, EV spread by
stat name and ability, a full per-checkpoint table, the complete movepool grouped by
source with ceiling and floor moves marked and unobtainable TMs faded, and the obtainment
table with method, level range and slot rate.

The payload gained the data that made this possible in `app/augment_payload.py`, a second
stage over `app/build_payload.py`: the full 933-move table with type, category, power,
priority and earliest obtainment gate; per-species movepools split into level-up, TM,
tutor and egg; per-species obtainment rows; the decoded type chart; lineage aggregates;
the zero-investment floor build's moves per checkpoint; structured evolution records
replacing the leaked JS template string; and four valuation columns that were parsed but
never exported — `replacement`, `sustain_depth`, the ceiling build's ability, and its EV
spread.

**One thing the card deliberately does not claim.** The reference interface annotates each
move with how many boss slots it was the best answer to. That figure cannot be rebuilt
from this bundle: the 2,698,734-cell matrix was summarised to one row per build before
export, so the per-slot best-move count no longer exists on disk. Recovering it means
re-running Phase 4 with a per-slot rollup added to the export. Likewise the sustain block
shows depth and kit delta but not the healing, hazard-chip and screen components, which
`09_sustain.js` computed and `05_valuation.tsv` did not carry.

## What the app does not show

Team coverage reads 100% at every checkpoint, because a threat counts as answered when
one member beats it one-on-one. That is a low bar and the figure is presented as a
ceiling rather than a promise.
