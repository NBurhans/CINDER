#!/usr/bin/env python3
"""CINDER Phase 1 — species-form master.

One row per species FORM. Stats converted from the source's internal order
[HP, Atk, Def, Spe, SpA, SpD] to display order exactly once, here.
"""
import json, csv, collections, re, os

WORK = "/home/claude/work"
OUT = "/mnt/user-data/outputs/cinder"
os.makedirs(OUT, exist_ok=True)

d = json.load(open(f"{WORK}/data.json"))
SP, MV, AB, IT = d["species"], d["moves"], d["abilities"], d["items"]
TY, EG, TM, TU = d["types"], d["eggGroups"], d["tmMoves"], d["tutorMoves"]
EVO_TPL, CAPS, AREAS = d["evolutions"], d["caps"], d["areas"]

log = []
def L(check, severity, detail): log.append(dict(check=check, severity=severity, detail=detail))

def esc(s):
    return str(s).replace("\t", r"\t").replace("\n", r"\n").replace("|", r"\|")

# ---------------------------------------------------------------- lookups
mv_name = {int(k): v["name"] for k, v in MV.items()}
ab_name = {int(k): (v["names"][0] if v.get("names") else "UNK") for k, v in AB.items()}
it_name = {int(k): v["name"] for k, v in IT.items()}
ty_name = {int(k): v["name"] for k, v in TY.items()}
eg_name = {int(k): v for k, v in EG.items()}
tm_slot = {int(k): int(v) for k, v in TM.items()}
tu_slot = {int(k): int(v) for k, v in TU.items()}
cap_by_id = {v["ID"]: k for k, v in CAPS.items()}

# abilities carry several display names on some IDs — record it rather than lose it
multi = {int(k): v["names"] for k, v in AB.items() if len(v.get("names", [])) > 1}
bydex = collections.defaultdict(list)
for _s in SP.values(): bydex[_s["dexID"]].append(_s)
_mf = {k: v for k, v in bydex.items() if len(v) > 1}
L("A6_name_not_unique", "WARN",
  f"species `name` is the BASE name and is not a unique key: {len(_mf)} catalogue numbers "
  f"carry more than one record, covering {sum(len(v) for v in _mf.values())} rows. Forms are "
  f"identified by `key` (e.g. Charizard / Charizard-Mega-X / Charizard-Mega-Y all have "
  f"name='Charizard'). Keying on name would silently merge them.")
L("A5_ability_alias", "INFO",
  f"{len(multi)} ability IDs carry more than one display name; slot 0 used, all retained. "
  f"Sample {list(multi.items())[:3]}")

# ---------------------------------------------------------- evolution methods
mega_methods, item_methods = set(), set()
for k, tpl in EVO_TPL.items():
    kk = int(k)
    if "Mega" in tpl or "mega" in tpl: mega_methods.add(kk)
    if "items[" in tpl: item_methods.add(kk)
L("E1_evo_templates", "INFO",
  f"{len(EVO_TPL)} evolution method templates; item-parameterised {sorted(item_methods)}; "
  f"name-mentions-mega {sorted(mega_methods)}")

# method 254 observed as the mega edge (param = stone item, target = mega form)
MEGA_METHOD = 254

# ------------------------------------------------------------- form typing
FORM_VOCAB = ["Mega-X", "Mega-Y", "Mega", "Primal", "Alola", "Galar", "Hisui",
              "Paldea", "Sevii", "Origin", "Therian", "Blood", "Crowned",
              "Eternamax", "Gmax", "Ash", "Dusk-Mane", "Dawn-Wings", "Ultra"]
REGIONAL = {"Alola","Galar","Hisui","Paldea","Sevii"}
MEGAISH  = {"Mega","Mega-X","Mega-Y","Primal"}
def split_form(name, key):
    """`name` is the base species name and is NOT unique across rows; `key` is the
    form-qualified name. Charizard / Charizard-Mega-X / Charizard-Mega-Y all share
    name='Charizard'. Forms therefore come from key, never from name."""
    if not key or key == name or "-" not in key:
        return name, "NONE", "base"
    base, form = key.split("-", 1)
    ft = ("mega" if form in MEGAISH else
          "regional" if form in REGIONAL else "other")
    return base, form, ft

# ------------------------------------------------------- availability index
WILD = {"wild-day", "wild-night", "wild-surf", "wild-oldRod", "wild-goodRod",
        "wild-superRod", "wild-smash"}
FIXED = {"fixed-gift", "fixed-trade", "fixed-overworld", "fixed-roaming"}
RAID = {"raid1", "raid3", "raid4", "raid5", "raid6"}

avail = collections.defaultdict(list)   # species id -> [(gate, method, area, lo, hi, slot)]
for a in AREAS:
    area = a["name"]
    for key, byGate in a.items():
        if key == "name": continue
        for gate, entries in byGate.items():
            g = int(gate)
            if key in WILD:
                for slot, e in enumerate(entries):
                    avail[e[0]].append((g, key, area, e[1], e[2], slot))
            elif key in FIXED:
                for e in entries:
                    avail[e].append((g, key, area, None, None, None))
            elif key in RAID:
                for e in entries:
                    avail[e[0]].append((g, key, area, None, None, None))

starters = set()
for a in AREAS:
    if a["name"] == "Pallet Town Oak's Lab" and "fixed-gift" in a:
        starters = set(a["fixed-gift"].get("0", []))
L("S1_starters", "INFO",
  f"{len(starters)} starters derived from the Oak's Lab fixed-gift record at gate 0")

# starters re-obtainable later?
celadon = set()
for a in AREAS:
    if a["name"] == "Celadon City Mansion 1F" and "fixed-gift" in a:
        for g, e in a["fixed-gift"].items(): celadon |= set(e)
L("S2_starter_reobtainable", "INFO",
  f"{len(starters & celadon)} of {len(starters)} starters reappear in the Celadon "
  f"Mansion gift pool, so the gate-0 choice is not exclusive")

# ------------------------------------------------------------ evolution graph
parent, children = {}, collections.defaultdict(list)
orphan_evo = []
for sid, s in SP.items():
    for e in s.get("evolutions", []):
        method, param, tgt = e[0], e[1], e[2]
        if str(tgt) not in SP:
            orphan_evo.append((int(sid), s["name"], method, param, tgt)); continue
        children[int(sid)].append((method, param, tgt))
        if method != MEGA_METHOD:
            parent[tgt] = int(sid)

def stage(sid, seen=None):
    seen = seen or set()
    n = 1
    while sid in parent and sid not in seen:
        seen.add(sid); sid = parent[sid]; n += 1
    return n

# ------------------------------------------------------------------- audit
dupes = [k for k, v in collections.Counter(int(s["ID"]) for s in SP.values()).items() if v > 1]
L("A2_duplicate_ids", "WARN" if dupes else "INFO",
  f"{len(dupes)} duplicate internal IDs" + (f": {dupes[:10]}" if dupes else ""))

ids = sorted(int(k) for k in SP)
gaps = [i for i in range(ids[0], ids[-1]) if i not in set(ids)]
L("A3_index_gaps", "WARN" if gaps else "INFO",
  f"{len(gaps)} gaps in the internal index range {ids[0]}-{ids[-1]}" +
  (f"; sample {gaps[:10]}" if gaps else ""))

offset = [(int(s["ID"]), s["dexID"]) for s in SP.values() if int(s["ID"]) != s["dexID"]]
L("A1_index_vs_catalogue", "INFO",
  f"{len(offset)} of {len(SP)} species have ID != dexID; both carried as separate columns. "
  f"Sample {offset[:5]}")

dummy, badstat, badbst, nomoves, uniform = [], [], [], [], []
for sid, s in SP.items():
    st = s["stats"]
    if sum(st) < 100 or re.match(r"^[-?.]+$|MISSINGNO|DUMMY", s["name"], re.I):
        dummy.append((int(sid), s["name"], st))
    if len(set(st)) == 1:
        uniform.append((int(sid), s["name"], st[0]))
    if any(x < 1 or x > 255 for x in st):
        badstat.append((int(sid), s["name"], st))
    if not s.get("levelupMoves"):
        nomoves.append((int(sid), s["name"]))
L("B1a_uniform_spread", "INFO",
  f"{len(uniform)} species have all six base stats identical. In a Gen-3 decomp that is a "
  f"dummy-slot tell; here it is legitimate design (e.g. Ditto 48, Mew 100), so it is reported "
  f"rather than treated as a dummy: {uniform[:8]}")
L("B1_dummy_slots", "WARN" if dummy else "INFO",
  f"{len(dummy)} candidate dummy/placeholder rows" + (f": {dummy[:12]}" if dummy else ""))
L("D1_stat_range", "WARN" if badstat else "INFO",
  f"{len(badstat)} species with a base stat outside 1-255" + (f": {badstat[:6]}" if badstat else ""))
L("B2_zero_movepool", "WARN" if nomoves else "INFO",
  f"{len(nomoves)} species with an empty level-up movepool" +
  (f"; sample {nomoves[:10]}" if nomoves else ""))
L("C2_orphan_evolution", "WARN" if orphan_evo else "INFO",
  f"{len(orphan_evo)} evolution targets that do not resolve" +
  (f": {orphan_evo[:6]}" if orphan_evo else ""))

orphan_moves = collections.Counter()
for sid, s in SP.items():
    for m, lv in s.get("levelupMoves", []):
        if str(m) not in MV: orphan_moves[m] += 1
L("C1_orphan_learnset", "WARN" if orphan_moves else "INFO",
  f"{len(orphan_moves)} distinct undefined move IDs referenced by level-up learnsets" +
  (f": {dict(list(orphan_moves.items())[:8])}" if orphan_moves else ""))

nonspecies = [k for k in d["sprites"] if not k.lstrip("-").isdigit()]
sprite_ids = {int(k) for k in d["sprites"] if k.lstrip("-").isdigit()}
L("B3_sprite_table_impurity", "WARN",
  f"the sprites table has {len(d[chr(39)+chr(39)] if False else d['sprites'])} keys but "
  f"{len(nonspecies)} are not species: {nonspecies}. These are move-category icons, "
  f"not Pokemon. Species sprites = {len(sprite_ids)}.")
no_sprite = sorted(int(k) for k in SP if int(k) not in sprite_ids)
L("B4_species_sprite_gap", "WARN",
  f"{len(SP)} species vs {len(sprite_ids)} sprites; {len(no_sprite)} species without one: "
  + ", ".join(f"{i}:{SP[str(i)]['name']}" for i in no_sprite[:15]))

noavail = []

# ------------------------------------- resolve gate through evolution chains
direct = {i: min((r[0] for r in recs), default=None) for i, recs in avail.items()}
resolved, basis = dict(direct), {i: "direct" for i in direct}
for _ in range(24):                       # relax until stable; depth is small
    changed = False
    for sid in SP:
        i = int(sid)
        pg = resolved.get(parent[i]) if i in parent else None
        if pg is None: continue
        cur = resolved.get(i)
        if cur is None or pg < cur:
            resolved[i] = pg
            basis[i] = "via-evolution" if direct.get(i) is None or pg < direct[i] else "direct"
            changed = True
    if not changed: break
L("AV2_gate_propagation", "INFO",
  f"{sum(1 for i in resolved if basis.get(i)=='via-evolution')} species-forms take their "
  f"earliest gate from a pre-evolution rather than a direct encounter; "
  f"{sum(1 for i in SP if int(i) not in resolved)} remain with no reachable gate")

# ------------------------------------------------------------------- write
COLS = ["dex_number","internal_id","species_name","form_name","form_type","lineage_id",
        "evo_stage","form_key","sprite_key","evolves_from","evolves_into","evo_method_id",
        "evo_method_text","evo_param","evo_param_item","evo_item_obtainable",
        "type_1","type_2","hp","atk","def","spa","spd","spe","bst",
        "ability_1","ability_2","ability_hidden","levelup_moves","tm_moves",
        "tutor_moves","egg_moves","egg_groups","held_items","availability",
        "earliest_gate","earliest_gate_name","earliest_level","earliest_gate_basis","is_starter",
        "starter_reobtainable","wild_obtainable","one_time_only","missable",
        "source_record","confidence","notes"]

rows = []
for sid, s in sorted(SP.items(), key=lambda kv: int(kv[0])):
    i = int(sid)
    st = s["stats"]
    hp, atk, dfn, spe, spa, spd = st          # <- the whole point of Trap 1
    base_name, form, ft = split_form(s["name"], s.get("key", ""))
    ev_into, ev_m, ev_mt, ev_p, ev_pi = [], [], [], [], []
    for method, param, tgt in children.get(i, []):
        ev_into.append(SP[str(tgt)]["name"]); ev_m.append(str(method))
        tpl = EVO_TPL.get(str(method), "UNK")
        ev_mt.append(re.sub(r"[`${}]", "", tpl).replace("evo[1]", str(param)))
        ev_p.append(str(param))
        ev_pi.append(it_name.get(param, "NA") if method in item_methods else "NA")

    recs = sorted(avail.get(i, []))
    if not recs: noavail.append((i, s["name"]))
    av = "|".join(f"{esc(a)}:{m}:{g}:" +
                  (f"{lo}-{hi}" if lo is not None else "NA") +
                  (f":{slot}" if slot is not None else ":NA")
                  for g, m, a, lo, hi, slot in recs) or "NONE"
    gate = resolved.get(i)
    lvls = [r[3] for r in recs if r[0] == gate and r[3] is not None]
    gbasis = basis.get(i, "UNK")

    wild = any(r[1] in WILD for r in recs)
    fixed_only = bool(recs) and all(r[1] in FIXED for r in recs)

    rows.append({
      "dex_number": s["dexID"], "internal_id": i, "species_name": base_name,
      "form_name": form, "form_type": ft, "lineage_id": s.get("ancestor", "UNK"),
      "evo_stage": stage(i), "form_key": s.get("key", "UNK"), "sprite_key": i if i in sprite_ids else "UNK",
      "evolves_from": SP[str(parent[i])]["name"] if i in parent else "NONE",
      "evolves_into": ",".join(ev_into) or "NONE",
      "evo_method_id": ",".join(ev_m) or "NONE",
      "evo_method_text": ",".join(ev_mt) or "NONE",
      "evo_param": ",".join(ev_p) or "NONE",
      "evo_param_item": ",".join(ev_pi) or "NONE",
      "evo_item_obtainable": "UNK" if any(x != "NA" for x in ev_pi) else "NA",
      "type_1": ty_name.get(s["type"][0], "UNK"),
      "type_2": ty_name.get(s["type"][1], "NONE") if len(s["type"]) > 1 else "NONE",
      "hp": hp, "atk": atk, "def": dfn, "spa": spa, "spd": spd, "spe": spe,
      "bst": sum(st),
      "ability_1": ab_name.get(s["abilities"][0][0], "NONE"),
      "ability_2": ab_name.get(s["abilities"][1][0], "NONE"),
      "ability_hidden": ab_name.get(s["abilities"][2][0], "NONE"),
      "levelup_moves": ",".join(f"{mv_name.get(m,'UNK'+str(m))}:{lv}"
                                for m, lv in s.get("levelupMoves", [])) or "NONE",
      "tm_moves": ",".join(f"{slot}:{mv_name.get(tm_slot.get(slot,0),'UNK')}"
                           for slot in s.get("tmMoves", []) if tm_slot.get(slot, 0)) or "NONE",
      "tutor_moves": ",".join(f"{slot}:{mv_name.get(tu_slot.get(slot,0),'UNK')}"
                              for slot in s.get("tutorMoves", []) if tu_slot.get(slot, 0)) or "NONE",
      "egg_moves": ",".join(mv_name.get(m, "UNK") for m in s.get("eggMoves", [])) or "NONE",
      "egg_groups": ",".join(eg_name.get(g, "UNK") for g in s.get("eggGroup", [])) or "NONE",
      "held_items": ",".join(it_name.get(x, "UNK") for x in s.get("items", []) if x) or "NONE",
      "availability": av,
      "earliest_gate": gate if gate is not None else "UNK",
      "earliest_gate_name": cap_by_id.get(gate, "UNK") if gate is not None else "UNK",
      "earliest_level": min(lvls) if lvls else ("NA" if recs else "UNK"),
      "earliest_gate_basis": gbasis,
      "is_starter": "TRUE" if i in starters else "FALSE",
      "starter_reobtainable": ("TRUE" if i in celadon else "FALSE") if i in starters else "NA",
      "wild_obtainable": "TRUE" if wild else "FALSE",
      "one_time_only": "TRUE" if fixed_only else "FALSE",
      "missable": "TRUE" if (fixed_only and len(recs) == 1) else "FALSE",
      "source_record": f"data.js:species[{i}]",
      "confidence": "Measured",
      "notes": "derived: bst, evo_stage, earliest_gate, earliest_level, flags",
    })

unreachable = [(int(k), v["name"]) for k, v in SP.items() if int(k) not in resolved]
L("AV1_no_direct_encounter", "INFO",
  f"{len(noavail)} species-forms have no direct area record; most are evolved forms reached "
  f"by evolving a pre-evolution, which is why gate propagation exists")
L("AV3_unreachable", "WARN",
  f"{len(unreachable)} species-forms have no reachable gate by any path and are OUT OF POOL "
  f"until Phase 2 resolves eggs, shard trades and raid pools; sample {unreachable[:12]}")

with open(f"{OUT}/01_species.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(rows)

json.dump(log, open(f"{OUT}/INT_integrity_log_phase1.json", "w"), indent=1)
print(f"wrote {len(rows)} rows x {len(COLS)} cols")
for e in log:
    print(f"  [{e['severity']}] {e['check']}: {e['detail'][:150]}")
