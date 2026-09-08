# Contributing

This is a personal analysis tool. It is public so the numbers can be checked, not
because it needs contributors. If you want to check something, the fastest route is
to rerun the pipeline and diff the output.

## Rules that are not negotiable

1. **Every number is computed, not recalled.** A remembered base stat, movepool or
   type chart is a hypothesis. Load the file, run the code, show the arithmetic. This
   target rebalances species, moves, abilities and typings wholesale, so recall is not
   merely unreliable — it is wrong in the direction that matters.
2. **No information is dropped.** If the source has it, the dataset has it. Empty
   fields carry a sentinel; excluded rows are named in the integrity log with a reason.
3. **`NA`, `NONE` and `UNK` never collapse.** `NONE` is a measurement, `UNK` is a gap,
   `NA` is a category error.
4. **Ambiguity is named, not smoothed.** Two sources disagreeing is a deliverable.
5. **Every claim carries a confidence tier** — Measured, Derived, Inferred, Asserted.
   The tier says how we know, never whether we know.
6. **Invariants describe the result; they never reshape it.** If a recommendation
   fails a threshold because it is genuinely the best build, the threshold is
   overridden in writing with the value and the reason. Swapping in a worse build to
   hit a number is falsification, not tuning.

## Rerunning

`pipeline/` is numbered in dependency order. Stages 05, 07–10 are Node and need the
damage-calc fork compiled; the rest are Python 3 with no third-party dependencies.
`tools/verify_calcs.js` should reproduce the engine before you trust anything
downstream of it.

## What does not belong here

The extracted source database, the documentation set, intermediate parse artifacts and
the target adapter skill are INTERNAL and never commit. See `VISION.md` §9. No ROM,
save file or game asset is redistributed.
