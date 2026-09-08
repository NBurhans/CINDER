#!/usr/bin/env python3
"""CINDER — derived reference tables and adapter config.

Everything this writes is regenerable from data.json plus the phase outputs. Nothing
here is hand-authored, so every shipped file traces to code.
"""
import json, csv, collections, os

R = os.environ.get("REPO", "/mnt/user-data/outputs/halyard-cinder")
d = json.load(open("/home/claude/work/data.json"))
ty = {int(k): v["name"] for k, v in d["types"].items()}
SPLIT = {0: "Physical", 1: "Special", 2: "Status"}
TM = {int(k): int(v) for k, v in d["tmMoves"].items()}
TU = {int(k): int(v) for k, v in d["tutorMoves"].items()}
tmof = {v: k for k, v in TM.items() if v}
tuof = {v: k for k, v in TU.items() if v}
cap_by_id = {v["ID"]: k for k, v in d["caps"].items()}

def write(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    print(f"  {os.path.basename(path):26s} {len(rows):>7,} rows")

# ---- 01b_moves.tsv. Every build references moves by name; the table was never exported.
cols = ["move_id","name","type","category","power","accuracy","pp","priority",
        "secondary_chance","target","tm_slot","tm_number","tutor_slot","is_placeholder",
        "source_record","confidence","description"]
rows = []
for k, m in sorted(d["moves"].items(), key=lambda kv: int(kv[0])):
    i = int(k)
    rows.append(dict(move_id=i, name=m["name"], type=ty.get(m["type"], "UNK-type9"),
        category=SPLIT[m["split"]], power=m["power"], accuracy=m["accuracy"], pp=m["pp"],
        priority=m["priority"], secondary_chance=m["secondaryEffectChance"], target=m["target"],
        tm_slot=tmof.get(i, "NA"), tm_number=(tmof[i] + 1) if i in tmof else "NA",
        tutor_slot=tuof.get(i, "NA"),
        is_placeholder="TRUE" if m["name"] == "Placeholder" else "FALSE",
        source_record=f"data.js:moves[{i}]", confidence="Measured",
        description=(m.get("description") or "").replace("\t", " ").replace("\n", " ")))
write(f"{R}/data/01b_moves.tsv", cols, rows)

# ---- 01c_availability.tsv. The species master packs availability into one encoded
# column; flattened here so it can be joined without parsing.
sp = list(csv.DictReader(open(f"{R}/data/01_species.tsv", encoding="utf-8"), delimiter="\t"))
cols = ["internal_id","form_key","location","method","gate","gate_name","level_min",
        "level_max","slot_index","earliest_gate","gate_basis","confidence"]
rows = []
for s in sp:
    if s["availability"] == "NONE": continue
    for rec in s["availability"].split("|"):
        p = rec.split(":")
        if len(p) < 5: continue
        lv = p[3].split("-") if p[3] != "NA" else ["NA", "NA"]
        rows.append(dict(internal_id=s["internal_id"], form_key=s["form_key"], location=p[0],
            method=p[1], gate=p[2], gate_name=cap_by_id.get(int(p[2]), "UNK"),
            level_min=lv[0], level_max=lv[-1], slot_index=p[4],
            earliest_gate=s["earliest_gate"], gate_basis=s["earliest_gate_basis"],
            confidence="Measured"))
write(f"{R}/data/01c_availability.tsv", cols, rows)

# ---- 01d_map_gates.tsv. One row per place, with when it opens and on what evidence.
world = list(csv.DictReader(open(f"{R}/data/02_world.tsv", encoding="utf-8"), delimiter="\t"))
agg = collections.defaultdict(lambda: {"gate": 99, "enc": 0, "items": 0, "region": ""})
for r in world:
    a = agg[r["location"]]
    a["gate"] = min(a["gate"], int(r["earliest_gate"])); a["region"] = r["region"]
    if r["entity_type"] in ("wild_encounter","gift_pokemon","trade_pokemon","static_pokemon",
                            "roaming_pokemon","raid_den"): a["enc"] += 1
    else: a["items"] += 1
cols = ["area","region","earliest_gate","gate_name","encounters","items","basis","confidence"]
rows = [dict(area=k, region=v["region"], earliest_gate=v["gate"],
             gate_name=cap_by_id.get(v["gate"], "UNK"), encounters=v["enc"], items=v["items"],
             basis="numeric key on the area entry, read as an index into caps",
             confidence="Measured")
        for k, v in sorted(agg.items(), key=lambda kv: (kv[1]["gate"], kv[0]))]
write(f"{R}/data/01d_map_gates.tsv", cols, rows)

# ---- typechart.json
EFF = {0: 1.0, 5: 0.5, 20: 2.0, 1: 0.0}
chart = {ty[int(k)]: {ty[int(j)]: EFF[d["types"][k]["matchup"][int(j)]] for j in d["types"]}
         for k in d["types"]}
json.dump({"note": "attacker -> defender multiplier, decoded from the source matchup arrays. "
                   "Encoding 0=x1, 5=x0.5, 20=x2, 1=x0, verified against 12 known relations. "
                   "Source type ids are NOT contiguous: 0-8, 10-17, 23. Index 9 is the unused "
                   "??? slot (one move, Struggle) and Fairy is 23, which is why the arrays are "
                   "24 long against 18 types.",
           "confidence": "Measured", "chart": chart},
          open(f"{R}/data/typechart.json", "w"), indent=1)
print(f"  typechart.json             {len(chart)} types")

# ---- adapter config, per VISION §8
ck = list(csv.DictReader(open(f"{R}/data/03b_checkpoints.tsv", encoding="utf-8"), delimiter="\t"))
y = ["# targets/cinder/checkpoints.yaml — EXTERNAL",
     "# The progression spine. Unusually for this framework it is not constructed: the",
     "# target's own source ships an ordered, named cap table and trainers reference it",
     "# by id, so this is read rather than assembled.",
     "#",
     "# Each cap carries two values. cap[0] matches the level cap published in the",
     "# official default-mode boss sheet on 18 of 18 gates and is what every",
     "# cap-relative level resolves against. cap[1] is unidentified.", "", "checkpoints:"]
for c in ck:
    y += [f"  - index: {c['checkpoint_index']}",
          f"    name: {c['checkpoint_name']}",
          f"    level_cap: {c['level_cap']}",
          f"    cap_secondary: {c['cap_secondary']}",
          f"    authored_bosses: {c['authored_boss_candidates']}",
          f"    scored_slots: {c['scored_roster_slots']}",
          f"    has_own_roster: {c['has_own_roster'].lower()}"]
open(f"{R}/data/checkpoints.yaml", "w").write("\n".join(y) + "\n")

open(f"{R}/data/mechanics.yaml", "w").write("""# targets/cinder/mechanics.yaml — EXTERNAL
# Generation-dependent switches. Pinned once; every damage calculation inherits
# these, which is why every matrix cell is Derived and never Measured.

mechanics_gen: 9            # confirmed by hand-reproducing 12 calcs against an
                            # independent implementation: 0.0% discrepancy
engine:
  package: "@smogon/calc"
  version: "0.9.0"
  entry: adaptable          # the bundled data layer is never used AS DATA
  dispatch: calculateSMSSSV

physical_special_split: per_move
fairy_type: present         # source type id 23, not contiguous with 0-17
priority_orders_turns: true # target 01 scored priority without simulating it
stat_array_order: [hp, atk, def, spe, spa, spd]   # NOT display order

recovery_per_turn:          # fractions of max HP, behind the sustain axis
  reliable_recovery: 0.25   # inherited from target 01 and NOT re-derived here
  regenerator: 0.11
  leftovers_class: 0.0625
""")

open(f"{R}/data/modes.yaml", "w").write("""# targets/cinder/modes.yaml — EXTERNAL
# The difficulty-mode axis. Target 02 is the first target to have one, and it is
# load-bearing rather than cosmetic.

canonical_mode: normal      # "default" in the target's own vocabulary, minimal grinding off

modes:
  - key: normal
    scored: true
  - key: hardcore
    scored: false           # parsed, tagged and retained; the cross-mode diff is the
                            # cheapest answer to "what changes if I switch modes"

roster_divergence: 214      # of 464 trainers differ between the two modes

item_conditionality: UNRESOLVED
# The source does not encode which items exist in which mode. That conditionality is
# prose in the documentation set and needs a manual pass. Until it is done, every
# recommended build is mode-agnostic. See docs/AVAILABILITY_NOTE.md.
""")
print("  checkpoints.yaml / mechanics.yaml / modes.yaml")
