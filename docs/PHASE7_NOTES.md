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

## What the app does not show

Team coverage reads 100% at every checkpoint, because a threat counts as answered when
one member beats it one-on-one. That is a low bar and the figure is presented as a
ceiling rather than a promise.
