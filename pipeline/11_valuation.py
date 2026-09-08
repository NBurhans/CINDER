#!/usr/bin/env python3
"""CINDER Phase 5 — valuation.

Gates before scores. role_fit = .25*S + .20*T + .15*Y + .40*F, all four reported.
Percentile-normalised within the obtainable pool at each checkpoint. VORP against
third-best obtainable at zero investment. Dead-weight penalty 0.50 on the early
checkpoints a lineage spends in an underperforming form.
"""
import csv, json, glob, collections, math, statistics

OUT = "/mnt/user-data/outputs/cinder"
W_STAT, W_TOOL, W_TYPE, W_FIGHT = .25, .20, .15, .40
# Utility roles are defined by tools and fight relevance, not by stats. Keeping a stat term
# for them made the cell score a BST ranking by construction: core=HP tracks BST, and T was
# near-constant because most pivots carry exactly one pivot move.
W_UTIL = dict(S=0.0, T=.30, Y=.20, F=.50)
DEADWEIGHT = 0.50
log = []
def L(c, s, t): log.append(dict(check=c, severity=s, detail=t))
L("V0_weights", "INFO", f"role_fit = {W_STAT}*S + {W_TOOL}*T + {W_TYPE}*Y + {W_FIGHT}*F; utility family {W_UTIL}; "
                        f"dead-weight penalty {DEADWEIGHT}; thresholds set numerically on the VORP distribution")

sp = {r["internal_id"]: r for r in csv.DictReader(open(f"{OUT}/01_species.tsv", encoding="utf-8"), delimiter="\t")}
mx = list(csv.DictReader(open(f"{OUT}/04_matchups.tsv", encoding="utf-8"), delimiter="\t"))
nat = {}
for f in glob.glob("/home/claude/work/na_*.json"):
    for r in json.load(open(f)): nat[(r["checkpoint"], r["internal_id"], r["track"])] = r["nature"]
for r in mx: r["nature"] = nat.get((r["checkpoint"], r["internal_id"], r["track"]), "UNK")
L("V0c_natures", "INFO",
  f"natures enumerated and MEASURED against the roster for {len(nat)} builds, replacing the "
  f"blanket Hardy that made I2 unmeasurable. Candidates are the natures that plausibly serve "
  f"each track, not all 25.")
fl = []
for f in glob.glob("/home/claude/work/fl_*.json"): fl += json.load(open(f))
floor = {}
for r in fl:
    k = (r["checkpoint"], r["internal_id"])
    if k not in floor or r["mean_margin"] > floor[k]["mean_margin"]: floor[k] = r
L("V0a_floor_matrix", "INFO", f"{len(fl)} floor builds run through the matrix so VORP's zero-investment "
                              f"baseline and ROI are measured rather than proxied")

trs = [t for t in csv.DictReader(open(f"{OUT}/03_trainers.tsv", encoding="utf-8"), delimiter="\t")
       if t["mode"] == "normal" and t["is_level_scaled"] == "FALSE" and int(t["party_size"]) >= 4]
roster_types = collections.defaultdict(list)
key2id = {v["form_key"]: k for k, v in sp.items()}
for t in trs:
    for nm in t["roster_species"].split(","):
        s = sp.get(key2id.get(nm, ""))
        if s: roster_types[t["cap_index"]].append([s["type_1"]] + ([s["type_2"]] if s["type_2"] != "NONE" else []))

d = json.load(open("/home/claude/work/data.json"))
tyname = {int(k): v["name"] for k, v in d["types"].items()}
tyid = {v: k for k, v in tyname.items()}
EFF = {0: 1.0, 5: 0.5, 20: 2.0, 1: 0.0}
matchup = {int(k): v["matchup"] for k, v in d["types"].items()}
UNTYPED = [v["name"] for v in d["moves"].values() if v["type"] not in tyname]
mvtype = {v["name"]: tyname[v["type"]] for v in d["moves"].values() if v["type"] in tyname}
L("V0b_type_keyspace", "INFO",
  f"the type table is NOT contiguous: ids 0-8, 10-17, 23. Index 9 is the unused ??? slot and "
  f"FAIRY IS 23, which is why the matchup array is 24 long and why Fighting carries a 0.5 at "
  f"index 23. That resolves the Phase 3 open item. {len(UNTYPED)} moves carry the unused type "
  f"and are excluded from coverage scoring.")
mvpow  = {v["name"]: v["power"] for v in d["moves"].values()}
mvsplit = {v["name"]: v["split"] for v in d["moves"].values()}
def eff(atk, dts):
    m = 1.0
    for dt in dts: m *= EFF[matchup[tyid[atk]][tyid[dt]]]
    return m

RECOV = {"Recover","Roost","Soft-Boiled","Moonlight","Morning Sun","Synthesis","Slack Off",
         "Milk Drink","Shore Up","Wish","Life Dew","Jungle Healing","Lunar Blessing","Rest"}
HAZ   = {"Stealth Rock","Spikes","Toxic Spikes","Sticky Web"}
REMOV = {"Rapid Spin","Defog","Mortal Spin","Court Change"}
STAT  = {"Will-O-Wisp","Thunder Wave","Toxic","Spore","Sleep Powder","Hypnosis","Glare","Nuzzle","Yawn"}
SCRN  = {"Reflect","Light Screen","Aurora Veil"}
PHAZ  = {"Roar","Whirlwind","Dragon Tail","Circle Throw"}
PIVOT = {"U-turn","Volt Switch","Teleport","Flip Turn","Parting Shot","Baton Pass"}
CLER  = {"Wish","Heal Bell","Aromatherapy","Healing Wish","Lunar Blessing"}
SPCTL = {"Tailwind","Trick Room","Sticky Web","Thunder Wave","Icy Wind","Electroweb"}

def prio(m): return 0
ROLES = {
 "wallbreaker_phys": dict(fam="off", core=lambda s: int(s["atk"]),
   gate=lambda b, s, mv, M: sum(1 for m in mv if mvsplit.get(m)==0 and mvpow.get(m,0)>=90) >= 2,
   tools=lambda mv: {m for m in mv if mvsplit.get(m)==0 and mvpow.get(m,0)>=90}),
 "wallbreaker_spec": dict(fam="off", core=lambda s: int(s["spa"]),
   gate=lambda b, s, mv, M: sum(1 for m in mv if mvsplit.get(m)==1 and mvpow.get(m,0)>=90) >= 2,
   tools=lambda mv: {m for m in mv if mvsplit.get(m)==1 and mvpow.get(m,0)>=90}),
 "setup_sweeper": dict(fam="off", core=lambda s: max(int(s["atk"]),int(s["spa"]))*0.5+int(s["spe"])*0.5,
   gate=lambda b, s, mv, M: b["setup_move"] != "NONE" and any(mvpow.get(m,0)>=75 for m in mv),
   tools=lambda mv: {m for m in mv if mvpow.get(m,0)>=75}),
 "revenge_killer": dict(fam="off", core=lambda s: int(s["spe"]),
   gate=lambda b, s, mv, M: float(b["switchin_safe_rate"]) >= 0.5 and any(mvpow.get(m,0)>=60 for m in mv),
   tools=lambda mv: {m for m in mv if mvpow.get(m,0)>=60}),
 "mixed_attacker": dict(fam="off", core=lambda s: (int(s["atk"])+int(s["spa"]))/2,
   gate=lambda b, s, mv, M: any(mvsplit.get(m)==0 and mvpow.get(m,0)>=75 for m in mv)
                     and any(mvsplit.get(m)==1 and mvpow.get(m,0)>=75 for m in mv)
                     and int(s["atk"]) > M["atk"] and int(s["spa"]) > M["spa"],
   tools=lambda mv: {m for m in mv if mvpow.get(m,0)>=75}),
 "physical_wall": dict(fam="def", core=lambda s: int(s["hp"])*int(s["def"])/100,
   gate=lambda b, s, mv, M: bool(RECOV & set(mv)) and int(s["hp"])*int(s["def"]) > M["hpdef"]
                     and bool(({"Will-O-Wisp","Intimidate"} | PHAZ) & set(mv)),
   tools=lambda mv: (RECOV|STAT|PHAZ) & set(mv)),
 "special_wall": dict(fam="def", core=lambda s: int(s["hp"])*int(s["spd"])/100,
   gate=lambda b, s, mv, M: bool(RECOV & set(mv)) and int(s["hp"])*int(s["spd"]) > M["hpspd"]
                     and bool((STAT | SCRN) & set(mv)),
   tools=lambda mv: (RECOV|STAT|SCRN) & set(mv)),
 "tank": dict(fam="def", core=lambda s: int(s["hp"])*min(int(s["def"]),int(s["spd"]))/100,
   gate=lambda b, s, mv, M: b["setup_move"]=="NONE"
                     and any(mvpow.get(m,0)>=75 for m in mv)
                     and int(s["hp"])*min(int(s["def"]),int(s["spd"])) > M["hpmin"]
                     and max(int(s["atk"]),int(s["spa"])) > M["off"]
                     and (b["ceiling_item_tag"] in ("assault_vest","contact_punish","longevity","eviolite")
                          or bool((RECOV|STAT|PIVOT) & set(mv))),
   tools=lambda mv: (RECOV|STAT|PIVOT|SCRN) & set(mv)),
 "hazard_setter": dict(fam="util", core=lambda s: int(s["hp"]),
   gate=lambda b, s, mv, M: bool(HAZ & set(mv)), tools=lambda mv: HAZ & set(mv)),
 "hazard_remover": dict(fam="util", core=lambda s: int(s["hp"]),
   gate=lambda b, s, mv, M: bool(REMOV & set(mv)), tools=lambda mv: REMOV & set(mv)),
 "status_spreader": dict(fam="util", core=lambda s: int(s["hp"]),
   gate=lambda b, s, mv, M: bool(STAT & set(mv)), tools=lambda mv: STAT & set(mv)),
 "screens_setter": dict(fam="util", core=lambda s: int(s["hp"]),
   gate=lambda b, s, mv, M: len(SCRN & set(mv)) >= 1, tools=lambda mv: SCRN & set(mv)),
 "phazer": dict(fam="util", core=lambda s: int(s["hp"])*int(s["def"])/100,
   gate=lambda b, s, mv, M: bool(PHAZ & set(mv))
                     and int(s["hp"])*int(s["def"]) > M["hpdef"],
   tools=lambda mv: (PHAZ|HAZ|RECOV) & set(mv)),
 "pivot": dict(fam="util", core=lambda s: int(s["hp"]),
   gate=lambda b, s, mv, M: bool(PIVOT & set(mv)), tools=lambda mv: PIVOT & set(mv)),
 "cleric": dict(fam="util", core=lambda s: int(s["hp"]),
   gate=lambda b, s, mv, M: bool(CLER & set(mv)), tools=lambda mv: CLER & set(mv)),
 "speed_control": dict(fam="util", core=lambda s: int(s["spe"]),
   gate=lambda b, s, mv, M: bool(SPCTL & set(mv)), tools=lambda mv: SPCTL & set(mv)),
}

def pctf(vals):
    s = sorted(vals); n = len(s)
    return lambda v: (sum(1 for x in s if x < v) / max(1, n-1))

rows = []
for cp in sorted({r["checkpoint"] for r in mx}, key=int):
    pool = [r for r in mx if r["checkpoint"] == cp]
    rts = roster_types.get(cp, [])
    marg = [float(r["mean_margin"]) for r in pool]
    pm = pctf(marg)
    corepct = {rn: pctf([R["core"](sp[r["internal_id"]]) for r in pool]) for rn, R in ROLES.items()}
    med = {k: statistics.median([int(sp[r["internal_id"]][k]) for r in pool])
           for k in ("atk","spa","def","spd","hp","spe")}
    med["hpdef"] = statistics.median([int(sp[r["internal_id"]]["hp"])*int(sp[r["internal_id"]]["def"]) for r in pool])
    med["hpspd"] = statistics.median([int(sp[r["internal_id"]]["hp"])*int(sp[r["internal_id"]]["spd"]) for r in pool])
    med["hpmin"] = statistics.median([int(sp[r["internal_id"]]["hp"])*min(int(sp[r["internal_id"]]["def"]),int(sp[r["internal_id"]]["spd"])) for r in pool])
    med["off"]   = statistics.median([max(int(sp[r["internal_id"]]["atk"]),int(sp[r["internal_id"]]["spa"])) for r in pool])
    for r in pool:
        s = sp[r["internal_id"]]
        mv = r["moves"].split(",")
        atk_types = {mvtype[m] for m in mv if m in mvtype and mvpow.get(m,0) > 0}
        Yoff = (sum(max((eff(t, dt) for t in atk_types), default=0) for dt in rts)/len(rts)/2) if rts and atk_types else 0
        Ydef = float(r["switchin_safe_rate"])
        F = pm(float(r["mean_margin"]))
        fkey = floor.get((cp, r["internal_id"]))
        for rn, R in ROLES.items():
            if not R["gate"](r, s, mv, med): continue
            S = corepct[rn](R["core"](s))
            tl = R["tools"](mv)
            T = min(1.0, len(tl) / (3.0 if R["fam"] != "util" else 2.0))
            Y = Yoff if R["fam"] == "off" else Ydef
            if R["fam"] == "util":
                w = W_UTIL; fit = w["T"]*T + w["Y"]*Y + w["F"]*F
            else:
                fit = W_STAT*S + W_TOOL*T + W_TYPE*Y + W_FIGHT*F
            rows.append(dict(checkpoint=cp, internal_id=r["internal_id"], form_key=r["form_key"],
                lineage_id=s["lineage_id"], role=rn, role_family=R["fam"], track=r["track"],
                S=round(S,4), T=round(T,4), Y=round(Y,4), F=round(F,4), role_fit=round(fit,4),
                ceiling_margin=float(r["mean_margin"]),
                floor_margin=float(fkey["mean_margin"]) if fkey else "UNK",
                roi=round(float(r["mean_margin"])-float(fkey["mean_margin"]),3) if fkey else "UNK",
                ceiling_item=r["ceiling_item"], item_dependence=r["item_dependence"],
                setup_move=r["setup_move"], nature=r["nature"], switchin_safe_rate=r["switchin_safe_rate"],
                moves=r["moves"], confidence="Derived"))

# ---- VORP against third-best obtainable at ZERO investment in each (checkpoint, role)
byc = collections.defaultdict(list)
for r in rows: byc[(r["checkpoint"], r["role"])].append(r)
undef = 0
for k, v in byc.items():
    fl_fits = sorted([x for x in v if x["floor_margin"] != "UNK"],
                     key=lambda x: -float(x["floor_margin"]))
    if len(fl_fits) >= 3:
        # replacement = the role_fit of the third-best ZERO-INVESTMENT build in the cell
        repl = sorted([x["role_fit"] for x in fl_fits[:3]])[0]
    else:
        repl = None; undef += 1
    for x in v:
        x["replacement"] = round(repl,4) if repl is not None else "UNK"
        x["vorp"] = round(x["role_fit"] - repl, 4) if repl is not None else "UNK"
L("V1_replacement", "WARN",
  f"{len(byc)} (checkpoint, role) cells; {undef} have fewer than 3 zero-investment builds so "
  f"replacement is undefined and VORP is suppressed rather than computed against an empty baseline")

scored = [r for r in rows if r["vorp"] != "UNK"]
vs = sorted(x["vorp"] for x in scored)
def q(p): return vs[int(p*(len(vs)-1))]
print(f"VORP distribution over {len(scored)} scored (form, checkpoint, role) rows:")
for p in (0.01,0.10,0.25,0.50,0.75,0.90,0.97,0.99,1.0):
    print(f"   p{int(p*100):>3} {q(p):+.4f}")
json.dump(log, open(f"{OUT}/INT_integrity_log_phase5.json","w"), indent=1)
json.dump(rows, open("/home/claude/work/valuation_rows.json","w"))
print(f"\nrows {len(rows)}  cells {len(byc)}  roles {len({r['role'] for r in rows})}")
