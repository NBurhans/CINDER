#!/usr/bin/env python3
"""CINDER — app payload, v2.

The reference interface filters and bands by ROLE, so it needs every scored
(form, checkpoint, role) row rather than one primary per form. Columnar, with every
repeated string coded to an integer, then gzipped.
"""
import json, csv, collections, gzip, base64, os

OUT = "/mnt/user-data/outputs/cinder"
_d = json.load(open("/home/claude/work/data.json"))
TYCOL = {v["name"]: v.get("color", "#6E7873") for v in _d["types"].values()}
tsv = lambda p: list(csv.DictReader(open(f"{OUT}/{p}", encoding="utf-8"), delimiter="\t"))
sp   = tsv("01_species.tsv"); world = tsv("02_world.tsv")
trn  = tsv("03_trainers.tsv"); ck = tsv("03b_checkpoints.tsv")
val  = tsv("05_valuation.tsv"); lin = tsv("05b_lineage.tsv"); teams = tsv("05c_teams.tsv")

# ---- string pools
pools = {k: ([], {}) for k in ("role","tier","item","nature","move","type","ability","area","setup")}
def code(pool, s):
    lst, idx = pools[pool]
    if s not in idx: idx[s] = len(lst); lst.append(s)
    return idx[s]

sid2i, species = {}, []
for i, s in enumerate(sp):
    sid2i[s["internal_id"]] = i
    species.append([
        s["form_key"], int(s["dex_number"]), code("type", s["type_1"]),
        code("type", s["type_2"]) if s["type_2"] != "NONE" else -1,
        int(s["hp"]), int(s["atk"]), int(s["def"]), int(s["spa"]), int(s["spd"]), int(s["spe"]),
        int(s["bst"]),
        code("ability", s["ability_1"]),
        code("ability", s["ability_2"]) if s["ability_2"] != "NONE" else -1,
        code("ability", s["ability_hidden"]) if s["ability_hidden"] != "NONE" else -1,
        "" if s["earliest_gate"] == "UNK" else int(s["earliest_gate"]),
        s["earliest_gate_basis"] if s["earliest_gate"] != "UNK" else "",
        s["evolves_from"] if s["evolves_from"] != "NONE" else "",
        s["evolves_into"] if s["evolves_into"] != "NONE" else "",
        s["evo_method_text"][:70] if s["evo_method_text"] != "NONE" else "",
        s["lineage_id"], int(s["internal_id"]) if s["sprite_key"] != "UNK" else -1,
        s["is_starter"] == "TRUE", s["missable"] == "TRUE", s["one_time_only"] == "TRUE",
        s["egg_groups"], s["form_type"],
    ])

# ---- every scored role row
rows = []
for r in val:
    if r["vorp"] == "UNK": continue
    rows.append([
        int(r["checkpoint"]), sid2i[r["internal_id"]], code("role", r["role"]),
        code("tier", r["tier"]), round(float(r["vorp"]), 3), round(float(r["role_fit"]), 3),
        round(float(r["S"]), 3), round(float(r["T"]), 3), round(float(r["Y"]), 3), round(float(r["F"]), 3),
        round(float(r["ceiling_margin"]), 2),
        round(float(r["floor_margin"]), 2) if r["floor_margin"] != "UNK" else None,
        round(float(r["roi"]), 2) if r["roi"] not in ("UNK","") else None,
        code("item", r["ceiling_item"]), code("nature", r["nature"]),
        [code("move", m) for m in r["moves"].split(",") if m],
        int(r["sustain_kit_delta"]) if r["sustain_kit_delta"] not in ("UNK","") else None,
        round(float(r["team_score"]), 3), round(float(r["switchin_safe_rate"]), 2),
        code("setup", r["setup_move"]) if r["setup_move"] != "NONE" else -1,
        round(float(r["item_dependence"]), 3) if r["item_dependence"] not in ("UNK","") else None,
        r["track"],
    ])

# ---- routes
routes = collections.defaultdict(lambda: {"g": 99, "e": [], "i": []})
for r in world:
    a = routes[r["location"]]; g = int(r["earliest_gate"])
    a["g"] = min(a["g"], g)
    if r["entity_type"] in ("wild_encounter","gift_pokemon","trade_pokemon","static_pokemon",
                            "roaming_pokemon","raid_den"):
        a["e"].append([r["entity_name"], r["acquisition_method"].replace("wild-",""), g,
                       r["encounter_rate"], r["level_min"], r["level_max"],
                       r["missable"] == "TRUE", r["star_tier"] if r["star_tier"] != "NA" else ""])
    else:
        a["i"].append([r["entity_name"], g, r["quantity"],
                       r["resolved_move"] if r["resolved_move"] != "NA" else ""])

# ---- bosses, grouped by checkpoint the way the reference groups fights
fights = collections.defaultdict(list)
for t in trn:
    if t["mode"] != "normal" or t["is_level_scaled"] != "FALSE" or int(t["party_size"]) < 4: continue
    fights[int(t["cap_index"])].append([
        t["name"], t["location"], int(t["party_size"]), int(t["max_level"]),
        [[n, ""] for n in t["roster_species"].split(",")],
        t["shared_weaknesses"], t["team_resisted_by"], t["offensive_types"], t["strategy_notes"]])

# ---- starters, ranked on the lineage aggregate over the whole run
prim = {}
for r in rows:
    k = (r[0], r[1])
    if k not in prim or r[5] > prim[k][5]: prim[k] = r
lid = {r["lineage_id"]: r for r in lin}
starters = []
for s in sp:
    if s["is_starter"] != "TRUE": continue
    lr = lid.get(s["lineage_id"])
    line = [x for x in sp if x["lineage_id"] == s["lineage_id"]]
    curve = {}
    for f in line:
        i = sid2i[f["internal_id"]]
        for cp in range(18):
            r = prim.get((cp, i))
            if r and (cp not in curve or r[4] > curve[cp]): curve[cp] = r[4]
    early = [curve[c] for c in (0,1,2) if c in curve]
    starters.append([s["form_key"], sid2i[s["internal_id"]],
        float(lr["lineage_vorp"]) if lr else 0.0, float(lr["dead_weight_penalty"]) if lr else 0.0,
        lr["comes_online_at"] if lr else "never",
        round(sum(early)/len(early), 3) if early else None, curve,
        s["starter_reobtainable"] == "TRUE", lr["forms"] if lr else s["form_key"]])
starters.sort(key=lambda x: -x[2])

payload = dict(
  meta=dict(
    cps=[[int(c["checkpoint_index"]), c["checkpoint_name"], int(c["level_cap"]),
          int(c["authored_boss_candidates"]), int(c["scored_roster_slots"])] for c in ck],
    roles=pools["role"][0], tiers=pools["tier"][0], items=pools["item"][0],
    natures=pools["nature"][0], moves=pools["move"][0], types=pools["type"][0],
    abilities=pools["ability"][0], setups=pools["setup"][0],
    typecolors=[TYCOL.get(t, "#6E7873") for t in pools["type"][0]],
    thresholds=[["S+",0.20],["S",0.12],["A",0.05],["B",-0.02],["C",-0.15],["D",-0.35]],
    weights="0.25 S · 0.20 T · 0.15 Y · 0.40 F   (utility family: 0.30 T · 0.20 Y · 0.50 F)",
    cells=2698734, ceilings=43934, scored=len(rows),
    invariants=[["I1","No held item in more than 25% of recommended builds","0.3234","≤ 0.25","overridden"],
                ["I2","No nature in more than 20%","0.2612","≤ 0.20","overridden"],
                ["I3","Rank is not a base-stat sort","0.5698","≤ 0.60","pass"],
                ["I4","Three options within 10% of the leader, every role, every fight","35 of 252 fail","0","overridden"],
                ["I5","Recommended teams are simultaneously equippable","17 of 17","100%","pass"],
                ["I6","Perturbing base stats changes the build","0.2074","≥ 0.20","pass"],
                ["I7","No move in more than 30% of movesets","0.1959","≤ 0.30","pass"]]),
  species=species, val=rows, routes=dict(routes),
  fights=[[k, [f for f in v]] for k, v in sorted(fights.items())],
  starters=starters,
  teams=[[int(t["checkpoint"]), t["members"], t["roles"], t["items"],
          int(t["threats_covered"]), int(t["threats"])] for t in teams],
)
raw = json.dumps(payload, separators=(",",":"))
b64 = base64.b64encode(gzip.compress(raw.encode(), 9)).decode()
d = json.load(open("/home/claude/work/data.json"))
spr = {k: v for k, v in d["sprites"].items() if k.isdigit()}
s64 = base64.b64encode(gzip.compress(json.dumps(spr, separators=(",",":")).encode(), 9)).decode()
open("/home/claude/work/payload2.b64","w").write(b64)
open("/home/claude/work/sprites.b64","w").write(s64)
print(f"payload {len(raw)/1e6:.2f} MB raw -> {len(b64)/1e6:.2f} MB encoded")
print(f"sprites -> {len(s64)/1e6:.2f} MB encoded")
print(f"species {len(species)}  scored rows {len(rows)}  routes {len(routes)}  "
      f"fights {sum(len(v) for v in fights.values())}  starters {len(starters)}")
print("pools:", {k: len(v[0]) for k, v in pools.items()})
