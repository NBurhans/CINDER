# Publishing

## Naming policy

Binding on everything in this repository:

- No franchise-identifying words in the repo name, description, topics, README title,
  or commit messages.
- The description stays generic: *"A data-driven planning framework for turn-based RPG
  progression."*
- Target folders and files use the codename, never the target's public name.
- Species, move and map names appear inside data files. That is unavoidable and
  accepted — the goal is that the repo is not findable by someone searching for the
  target, not that the contents are obfuscated.
- No topics or tags. No links from any forum, Discord or wiki.
- No ROM, save file or game asset. Derived numeric tables only.

## The known leak

The damage engine is a public fork whose repository name identifies the target, and
the README cites it as a dependency. Three options, none free: pin by commit hash
without the owner name, vendor the mechanics files, or accept it on the grounds that a
dependency URL is not a search term anyone would use to find this repo.

**Currently accepting**, recorded here so the decision is deliberate rather than an
oversight.

## Before pushing

- `docs/RUNBOOK.md` ships as a template. Confirm §0 is empty — the filled block names
  the target in plain language and is INTERNAL.
- The target adapter skill must not be in the tree. `tools/skill/` is the core
  analysis skill, which is target-agnostic and EXTERNAL.
- Grep the tree for the target's public name and for the source directory name. Both
  should return nothing.
- Regenerate `CHECKSUMS.txt` after any data change.

## GitHub Pages

`.nojekyll` is present so the underscore-prefixed paths are served. `index.html` is
self-contained and needs no build step. Replace the placeholder username in the
README link before publishing.
