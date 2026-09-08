#!/usr/bin/env python3
"""CINDER Phase 6 — evaluation. No new dataset. Re-read everything and try to break it."""
import csv, json, glob, collections, random, statistics

OUT = "/mnt/user-data/outputs/cinder"
log = []
def L(c, s, t): log.append(dict(check=c, severity=s, detail=t))
def load(p): return list(csv.DictReader(open(f"{OUT}/{p}", encoding="utf-8"), delimiter="\t"))

# ---------- 1. round-trip
files = ["01_species.tsv","02_world.tsv","03_trainers.tsv","03b_checkpoints.tsv",
         "04_matchups.tsv","04a_builds.tsv","05_valuation.tsv","05b_lineage.tsv"]
data = {}
print("ROUND-TRIP")
for f in files:
    rows = load(f); data[f] = rows
    ncol = len(rows[0]); ragged = sum(1 for r in rows if len(r) != ncol or any(v is None for v in r.values()))
    print(f"   {f:24s} {len(rows):>7,} rows x {ncol:>2} cols   ragged {ragged}")
    L("E1_round_trip", "WARN" if ragged else "INFO",
      f"{f}: {len(rows)} rows, {ncol} cols, {ragged} ragged")

# ---------- 2. cross-phase referential integrity
sp = {r["internal_id"]: r for r in data["01_species.tsv"]}
keys = {r["form_key"] for r in data["01_species.tsv"]}
world = data["02_world.tsv"]
item_gate = collections.defaultdict(lambda: 99)
for r in world:
    if r["entity_type"].startswith(("item_","vendor_")):
        item_gate[r["entity_name"]] = min(item_gate[r["entity_name"]], int(r["earliest_gate"]))
bad_species = [r for r in data["03_trainers.tsv"]
               for nm in r["roster_species"].split(",") if nm not in keys]
val = data["05_valuation.tsv"]
bad_item = [r for r in val if r["ceiling_item"] not in ("NONE","")
            and item_gate[r["ceiling_item"]] > int(r["checkpoint"])]
bad_form = [r for r in val if r["form_key"] not in keys]
print(f"\nCROSS-PHASE REFERENTIAL INTEGRITY")
print(f"   roster species not in the species table          {len(bad_species)}")
print(f"   ceiling forms not in the species table           {len(bad_form)}")
print(f"   ceiling items not obtainable by their checkpoint {len(bad_item)}")
L("E2_referential", "WARN" if (bad_species or bad_item or bad_form) else "INFO",
  f"roster species unresolved {len(bad_species)}; ceiling forms unresolved {len(bad_form)}; "
  f"ceiling items used before they are obtainable {len(bad_item)}"
  + (f"; sample {[(r['form_key'], r['ceiling_item'], r['checkpoint']) for r in bad_item[:5]]}" if bad_item else ""))

# ---------- 3. missing-data sweep
print(f"\nMISSING-DATA SWEEP — UNK by column")
for f in files:
    unk = collections.Counter()
    for r in data[f]:
        for k, v in r.items():
            if v == "UNK": unk[k] += 1
    if unk:
        print(f"   {f}")
        for k, n in unk.most_common():
            print(f"      {k:24s} {n:>7,}  ({100*n/len(data[f]):.1f}%)")
        L("E3_unk_sweep", "WARN", f"{f}: " + "; ".join(f"{k}={n}" for k, n in unk.most_common()))
mode_unk = sum(1 for r in world if r["mode_availability"] == "UNK")
L("E3a_mode_availability", "WARN",
  f"mode_availability is UNK on {mode_unk} of {len(world)} world rows. Not recoverable from the "
  f"extracted database; it lives as prose in the official item sheet and needs a manual pass. "
  f"It gates ceiling builds, so every ceiling is currently mode-agnostic.")


import json
json.dump(log, open(f"{OUT}/../halyard-cinder/docs/integrity_log_phase6.json","w"), indent=1)
print(f"\nlogged {len(log)} entries")
