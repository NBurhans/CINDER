#!/usr/bin/env python3
"""CINDER Phase 2 — world, items, and interactions. One row per acquirable thing."""
import json, csv, collections, re, os

WORK, OUT = "/home/claude/work", "/mnt/user-data/outputs/cinder"
d = json.load(open(f"{WORK}/data.json"))
SP, MV, IT = d["species"], d["moves"], d["items"]
TM = {int(k): int(v) for k, v in d["tmMoves"].items()}
TU = {int(k): int(v) for k, v in d["tutorMoves"].items()}
mv = {int(k): v["name"] for k, v in MV.items()}
it = {int(k): v["name"] for k, v in IT.items()}
sp_key = {int(k): v.get("key", v["name"]) for k, v in SP.items()}
cap_by_id = {v["ID"]: k for k, v in d["caps"].items()}

log = []
def L(c, s, t): log.append(dict(check=c, severity=s, detail=t))
def esc(s): return str(s).replace("\t", r"\t").replace("\n", r"\n").replace("|", r"\|")

# ---- encounter rate ladders. Source: the official locations sheet -> Asserted.
LADDER = {"wild-day":       [20,20,10,10,10,10,5,5,4,4,1,1],
          "wild-night":     [20,20,10,10,10,10,5,5,4,4,1,1],
          "wild-oldRod":    [70,30],
          "wild-goodRod":   [60,20,20],
          "wild-superRod":  [40,40,15,4,1],
          "wild-surf":      [60,30,5,4,1]}
for k, v in LADDER.items():
    assert sum(v) == 100, k
L("W1_rate_ladders", "INFO",
  "rate ladders taken from the official locations sheet, not from source, so every rate is "
  "Asserted while the species, level band and slot index on the same row are Measured. "
  + "; ".join(f"{k} {len(v)} slots" for k, v in LADDER.items()))

SEVII = ("One Island","Two Island","Three Island","Kindle Road","Treasure Beach","Mt Ember",
         "Cape Brink","Bond Bridge","Berry Forest","Three Isle","Ember Spa","Icefall","Lost Cave")
def region(area): return "Sevii" if any(area.startswith(s) for s in SEVII) else "Kanto"

WILD = set(LADDER) | {"wild-smash"}
FIXED = {"fixed-gift":"gift_pokemon","fixed-trade":"trade_pokemon",
         "fixed-overworld":"static_pokemon","fixed-roaming":"roaming_pokemon"}
ITEMS = {"item-standard":"item_ground","item-hidden":"item_hidden",
         "item-shop":"vendor_stock","item-cheat":"item_care_package"}
RAID = {"raid1":1,"raid3":3,"raid4":4,"raid5":5,"raid6":6}

rows, bad_rate, unknown_ladder = [], 0, collections.Counter()

def add(**kw):
    r = {c: "NA" for c in COLS}; r.update(kw); rows.append(r)

COLS = ["entity_type","entity_name","internal_id","location","region","acquisition_method",
        "cost","currency","quantity","prerequisites","earliest_gate","earliest_gate_name",
        "mode_availability","encounter_rate","level_min","level_max","slot_index","star_tier",
        "tm_number","resolved_move","raid_drops","missable","missable_reason",
        "source_record","confidence","notes"]

for a in d["areas"]:
    area, reg = a["name"], region(a["name"])
    for key, byGate in a.items():
        if key == "name" or key == "trainers": continue
        for gate, entries in byGate.items():
            g = int(gate); gname = cap_by_id.get(g, "UNK")
            src = f"data.js:areas[{esc(area)}].{key}[{g}]"

            if key in WILD:
                lad = LADDER.get(key)
                if lad and len(entries) != len(lad):
                    unknown_ladder[f"{key}:{len(entries)}slots"] += 1; lad = None
                if key == "wild-smash": lad = None
                for slot, e in enumerate(entries):
                    add(entity_type="wild_encounter", entity_name=sp_key.get(e[0], f"UNK{e[0]}"),
                        internal_id=e[0], location=esc(area), region=reg, acquisition_method=key,
                        quantity="REPEATABLE", earliest_gate=g, earliest_gate_name=gname,
                        mode_availability="UNK",
                        encounter_rate=(lad[slot] if lad else "UNK"),
                        level_min=e[1], level_max=e[2], slot_index=slot,
                        missable="FALSE", missable_reason="NA", source_record=src,
                        confidence="Measured",
                        notes="rate Asserted from the locations sheet" if lad else "ladder unresolved")

            elif key in FIXED:
                one_time = key in ("fixed-gift", "fixed-overworld")
                for e in entries:
                    add(entity_type=FIXED[key], entity_name=sp_key.get(e, f"UNK{e}"),
                        internal_id=e, location=esc(area), region=reg, acquisition_method=key,
                        quantity=1, earliest_gate=g, earliest_gate_name=gname,
                        mode_availability="UNK",
                        missable="TRUE" if one_time else "FALSE",
                        missable_reason="one-time placement" if one_time else "NA",
                        source_record=src, confidence="Measured", notes="NONE")

            elif key in ITEMS:
                shop = key == "item-shop"
                for e in entries:
                    name = it.get(e, f"UNK{e}")
                    tmno = rmove = "NA"
                    m = re.match(r"^TM(\d+)$", name)
                    if m:
                        tmno = int(m.group(1))
                        rmove = mv.get(TM.get(tmno - 1, 0), "UNK")   # TM01 <-> slot 0
                    add(entity_type=ITEMS[key], entity_name=name, internal_id=e,
                        location=esc(area), region=reg, acquisition_method=key,
                        cost="UNK" if shop else "NA", currency="money" if shop else "NA",
                        quantity="UNLIMITED" if shop else 1,
                        earliest_gate=g, earliest_gate_name=gname, mode_availability="UNK",
                        tm_number=tmno, resolved_move=rmove,
                        missable="FALSE" if shop else "TRUE",
                        missable_reason="NA" if shop else "single placement",
                        source_record=src, confidence="Measured",
                        notes="care-package item, delivered by code not exploration"
                              if key == "item-cheat" else "NONE")

            elif key == "tutors":
                for e in entries:
                    add(entity_type="tutor", entity_name=f"tutor_slot_{e}", internal_id=e,
                        location=esc(area), region=reg, acquisition_method="tutor",
                        cost="UNK", currency="money", quantity="REPEATABLE",
                        earliest_gate=g, earliest_gate_name=gname, mode_availability="UNK",
                        resolved_move=mv.get(TU.get(e, 0), "UNK"),
                        missable="FALSE", missable_reason="NA", source_record=src,
                        confidence="Measured", notes="value is a tutorMoves slot index, not a move ID")

            elif key in RAID:
                for e in entries:
                    add(entity_type="raid_den", entity_name=sp_key.get(e[0], f"UNK{e[0]}"),
                        internal_id=e[0], location=esc(area), region=reg,
                        acquisition_method=key, quantity="REPEATABLE",
                        earliest_gate=g, earliest_gate_name=gname, mode_availability="UNK",
                        star_tier=RAID[key],
                        raid_drops=",".join(it.get(x, f"UNK{x}") for x in e[1] if x) or "NONE",
                        prerequisites="Wishing Piece to re-activate a spent den",
                        missable="FALSE", missable_reason="NA", source_record=src,
                        confidence="Measured", notes="NONE")

L("W2_unknown_ladder", "WARN" if unknown_ladder else "INFO",
  f"encounter tables whose slot count does not match the published ladder, rates left UNK: "
  f"{dict(unknown_ladder)}" if unknown_ladder else "every table matched its published ladder")

# ---- TM coverage and the documented off-by-one
tm_rows = [r for r in rows if r["tm_number"] != "NA"]
placed = {r["tm_number"] for r in tm_rows}
L("W3_tm_offset", "INFO",
  f"TM item names are 1-indexed (TM01..) while the tmMoves table is 0-indexed; TM number N "
  f"resolves through slot N-1. {len(placed)} distinct TMs placed across {len(tm_rows)} rows. "
  f"Spot check: TM01 -> {mv.get(TM.get(0,0))}, TM39 -> {mv.get(TM.get(38,0))}")

missing_tm = [n for n in range(1, 121) if n not in placed]
L("W4_unplaced_tms", "WARN" if missing_tm else "INFO",
  f"{len(missing_tm)} TMs numbered 1-120 have no placement in any area: {missing_tm}")

# ---- does Phase 2 close the Phase 1 gap?
reachable = {int(r["internal_id"]) for r in rows
             if r["entity_type"] in ("wild_encounter","gift_pokemon","trade_pokemon",
                                     "static_pokemon","roaming_pokemon","raid_den")}
L("W5_species_channels", "INFO",
  f"{len(reachable)} distinct species-forms have at least one acquisition channel in the areas array")

# ---- evolution items referenced by Phase 1
evo_items = set()
for s in SP.values():
    for e in s.get("evolutions", []):
        if e[0] in (7, 254): evo_items.add(it.get(e[1], f"UNK{e[1]}"))
placed_items = {r["entity_name"] for r in rows if r["entity_type"].startswith(("item_","vendor_"))}
missing_evo = sorted(evo_items - placed_items)
L("W6_evolution_items", "WARN" if missing_evo else "INFO",
  f"{len(evo_items)} distinct evolution items referenced by species evolutions; "
  f"{len(missing_evo)} have no placement anywhere: {missing_evo[:20]}")

L("W7_mode_availability", "WARN",
  "mode_availability is UNK on every row. The extracted database does not encode difficulty-mode "
  "conditionality; the official item sheet marks it in prose ((HARDCORE) Unavailable, "
  "(DEFAULT MODE ONLY), MGM/HARDCORE variants). Filling this column is a manual pass against the "
  "doc set and it is Asserted when done. It gates ceiling builds in Phase 5, not scoring in Phase 3.")

L("W8_cost_unknown", "INFO",
  "shop prices are absent from the extracted database and are carried as UNK; the official item "
  "sheet publishes them and would be Asserted")

with open(f"{OUT}/02_world.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(rows)
json.dump(log, open(f"{OUT}/INT_integrity_log_phase2.json", "w"), indent=1)

print(f"wrote {len(rows)} rows x {len(COLS)} cols")
by = collections.Counter(r["entity_type"] for r in rows)
for k, v in by.most_common(): print(f"   {k:20s} {v}")
print()
for e in log: print(f"  [{e['severity']}] {e['check']}: {e['detail'][:165]}")
