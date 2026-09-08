#!/usr/bin/env python3
"""CINDER — payload v3.

Takes the payload already embedded in index.html and adds everything the
species card needs but never carried: full move table with type/category/power,
per-species movepools split by source, per-move obtainability gate, the type
chart, per-species availability rows with rates, lineage aggregates, the
zero-investment floor build's moves, and the four valuation columns that were
parsed but dropped (replacement, sustain depth, ceiling ability, EV spread).
"""
import csv, gzip, json, collections, sys

D    = "/home/claude/hc/data"
tsv  = lambda p: list(csv.DictReader(open(f"{D}/{p}", encoding="utf-8"), delimiter="\t"))
gtsv = lambda p: list(csv.DictReader(gzip.open(f"{D}/{p}", "rt", encoding="utf-8"), delimiter="\t"))

P = json.load(open("/home/claude/payload.json"))
M = P["meta"]

sp    = tsv("01_species.tsv")
moves = tsv("01b_moves.tsv")
world = tsv("02_world.tsv")
lin   = tsv("05b_lineage.tsv")
val   = gtsv("05_valuation.tsv.gz")
bld   = gtsv("04a_builds.tsv.gz")
chart = json.load(open(f"{D}/typechart.json"))["chart"]

types = M["types"]
tyi   = {t: i for i, t in enumerate(types)}
sid2i = {}
for i, s in enumerate(sp):
    sid2i[s["internal_id"]] = i
assert len(sid2i) == len(P["species"]), (len(sid2i), len(P["species"]))

# ---------------------------------------------------------------- move table
CAT = {"physical": 0, "special": 1, "status": 2}
mvname, mvi = [], {}
mvt, mvc, mvp, mvpr = [], [], [], []
for m in moves:
    if m["name"] in mvi:
        continue
    mvi[m["name"]] = len(mvname)
    mvname.append(m["name"])
    mvt.append(tyi.get(m["type"], -1))
    mvc.append(CAT.get(m["category"], 2))
    try:    mvp.append(int(m["power"]))
    except Exception: mvp.append(0)
    try:    mvpr.append(int(m["priority"]))
    except Exception: mvpr.append(0)

def mcode(name):
    """Any move name reaching the payload must exist in the move table."""
    if name not in mvi:
        mvi[name] = len(mvname)
        mvname.append(name); mvt.append(-1); mvc.append(2); mvp.append(0); mvpr.append(0)
    return mvi[name]

# earliest gate at which each TM/tutor move can be held
mvg = [-1] * len(mvname)
for r in world:
    mv = r["resolved_move"]
    if mv in ("NA", "", "UNK"):
        continue
    try: g = int(r["earliest_gate"])
    except Exception: continue
    i = mcode(mv)
    mvg[i] = g if mvg[i] < 0 else min(mvg[i], g)
mvg += [-1] * (len(mvname) - len(mvg))

# ------------------------------------------------------------- movepools
def pairs(cell):
    out = []
    if cell in ("NONE", "NA", "UNK", ""):
        return out
    for tok in cell.split(","):
        name, _, lvl = tok.rpartition(":")
        if name:
            out.append([mcode(name), int(lvl)])
    return out

def slotted(cell):
    out = []
    if cell in ("NONE", "NA", "UNK", ""):
        return out
    for tok in cell.split(","):
        slot, _, name = tok.partition(":")
        if name:
            out.append([mcode(name), int(slot)])
    return out

def plain(cell):
    if cell in ("NONE", "NA", "UNK", ""):
        return []
    return [mcode(t) for t in cell.split(",") if t]

pool = []
for s in sp:
    pool.append([pairs(s["levelup_moves"]), slotted(s["tm_moves"]),
                 slotted(s["tutor_moves"]), plain(s["egg_moves"])])

# ------------------------------------------------------------ availability
locs, loci, meth, methi = [], {}, [], {}
def lc(x):
    if x not in loci: loci[x] = len(locs); locs.append(x)
    return loci[x]
def mc(x):
    if x not in methi: methi[x] = len(meth); meth.append(x)
    return methi[x]

avail = collections.defaultdict(list)
POKE = {"wild_encounter", "gift_pokemon", "trade_pokemon", "static_pokemon",
        "roaming_pokemon", "raid_den"}
for r in world:
    if r["entity_type"] not in POKE:
        continue
    i = sid2i.get(r["internal_id"])
    if i is None:
        continue
    def num(k):
        v = r[k]
        try: return int(v)
        except Exception: return None
    avail[i].append([lc(r["location"]), mc(r["acquisition_method"]),
                     num("earliest_gate"), num("level_min"), num("level_max"),
                     num("encounter_rate"), r["missable"] == "TRUE"])
for k in avail:
    avail[k].sort(key=lambda x: (x[2] if x[2] is not None else 99, -(x[5] or 0)))

# ------------------------------------------------------------- type chart
tc = [[chart.get(a, {}).get(d, 1) for d in types] for a in types]

# --------------------------------------------------------------- lineage
lineage = {r["lineage_id"]: [round(float(r["raw_mean_vorp"]), 3),
                             round(float(r["dead_weight_penalty"]), 3),
                             round(float(r["lineage_vorp"]), 3),
                             r["comes_online_at"], r["forms"],
                             int(r["checkpoints"])] for r in lin}

# ------------------------------------------- floor builds and ceiling extras
evs, evsi = [], {}
def ec(x):
    if x not in evsi: evsi[x] = len(evs); evs.append(x)
    return evsi[x]

abi = {a: i for i, a in enumerate(M["abilities"])}
def ac(a):
    if a in ("NONE", "NA", "", "UNK"): return -1
    if a not in abi:
        abi[a] = len(M["abilities"]); M["abilities"].append(a)
    return abi[a]

floor, ceil = {}, {}
for b in bld:
    i = sid2i.get(b["internal_id"])
    if i is None: continue
    cp = int(b["checkpoint"])
    if b["anchor"] == "floor":
        floor[f"{cp}_{i}"] = [ac(b["ability"]), plain(b["moves"])]
    else:
        ceil[(cp, i, b["track"])] = [ac(b["ability"]), ec(b["ev_spread"]),
                                     b["track_reason"]]

trs, trsi = [], {}
def tc_(x):
    if x not in trsi: trsi[x] = len(trs); trs.append(x)
    return trsi[x]

# ------------------------------------------- extend every scored valuation row
key = {}
for r in val:
    if r["vorp"] == "UNK": continue
    key[(int(r["checkpoint"]), sid2i[r["internal_id"]], r["role"])] = r

role_names = M["roles"]
V_CP, V_SP, V_ROLE, V_TRACK = 0, 1, 2, 21
added = missing = 0
for row in P["val"]:
    r = key.get((row[V_CP], row[V_SP], role_names[row[V_ROLE]]))
    c = ceil.get((row[V_CP], row[V_SP], row[V_TRACK]))
    if r is None or c is None:
        row.extend([-1, -1, None, None, -1]); missing += 1; continue
    def f(k, nd=3):
        v = r[k]
        return None if v in ("UNK", "", "NA") else round(float(v), nd)
    row.extend([c[0], c[1], f("replacement"),
                int(r["sustain_depth"]) if r["sustain_depth"] not in ("UNK", "", "NA") else None,
                tc_(c[2])])
    added += 1

# ------------------------------------------------------------------- remap
# meta.moves was a 501-name build pool; everything now indexes the full table.
old = M["moves"]
remap = [mcode(n) for n in old]
V_MOVES = 15
for row in P["val"]:
    row[V_MOVES] = [remap[m] for m in row[V_MOVES]]

M["moves"]   = mvname
M["mvtype"]  = mvt
M["mvcat"]   = mvc
M["mvpow"]   = mvp
M["mvprio"]  = mvpr
M["mvgate"]  = mvg
M["evspreads"] = evs
M["trackreasons"] = trs
M["locs"]    = locs
M["methods"] = meth
M["typechart"] = tc
M["cardlimits"] = (
  "Per-move 'best answer to N boss slots' is not shown: the 2,698,734-cell matrix "
  "was summarised to one row per build before export, so the per-slot best-move "
  "count no longer exists in this bundle. Sustain shows depth and kit delta; "
  "the healing/hazard/screen components were not carried into 05_valuation.tsv.")

# structured evolution, so the card stops printing the leaked JS template
evo = {}
for i, s_ in enumerate(sp):
    if s_["evo_method_id"] in ("NONE", "NA", ""):
        continue
    ids  = s_["evo_method_id"].split(",")
    par  = s_["evo_param"].split(",")
    itm  = s_["evo_param_item"].split(",")
    tgt  = s_["evolves_into"].split(",")
    rec = []
    for j in range(len(ids)):
        rec.append([int(ids[j]),
                    par[j] if j < len(par) else "",
                    "" if j >= len(itm) or itm[j] in ("NA", "NONE") else itm[j],
                    tgt[j] if j < len(tgt) else ""])
    evo[str(i)] = rec

P["evo"]     = evo
P["pool"]    = pool
P["avail"]   = {str(k): v for k, v in avail.items()}
P["lineage"] = lineage
P["floor"]   = floor

raw = json.dumps(P, separators=(",", ":"))
open("/home/claude/payload3.json", "w").write(raw)
print(f"moves {len(mvname)} (was {len(old)})  gated {sum(1 for g in mvg if g>=0)}")
print(f"pool species {len(pool)}  avail species {len(avail)}  lineage {len(lineage)}")
print(f"floor builds {len(floor)}  ceiling joins ok {added}  unmatched {missing}")
print(f"ev spreads {evs}")
print(f"evolutions {len(evo)}")
print(f"raw payload {len(raw)/1e6:.2f} MB")
