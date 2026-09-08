#!/usr/bin/env python3
"""CINDER Phase 5 — tiers, sustain, lineage, invariants, export."""
import csv, json, glob, collections, statistics, itertools, random

OUT = "/mnt/user-data/outputs/cinder"
DEADWEIGHT = 0.50
TIERS = [("S+", 0.20), ("S", 0.12), ("A", 0.05), ("B", -0.02), ("C", -0.15), ("D", -0.35)]

rows = json.load(open("/home/claude/work/valuation_rows.json"))
log = json.load(open(f"{OUT}/INT_integrity_log_phase5.json"))
def L(c, s, t): log.append(dict(check=c, severity=s, detail=t))

sus = {}
for f in glob.glob("/home/claude/work/su_*.json"):
    for r in json.load(open(f)): sus[(r["checkpoint"], r["internal_id"])] = r
L("V2_sustain", "INFO",
  f"sustain computed for {len(sus)} (form, checkpoint) pairs: sequential lifebar in roster order, "
  f"reset at every trainer boundary, published as the kit delta. DEVIATION: the vision says read "
  f"turns-to-KO off the matrix cells; the matrix stored aggregates rather than per-slot cells, so "
  f"this recomputes them from the same engine and inputs. Same formula, second implementation.")

sp = {r["internal_id"]: r for r in csv.DictReader(open(f"{OUT}/01_species.tsv", encoding="utf-8"), delimiter="\t")}

def tier(v):
    for name, cut in TIERS:
        if v >= cut: return name
    return "F"

scored = [r for r in rows if r["vorp"] != "UNK"]
for r in rows:
    r["tier"] = tier(r["vorp"]) if r["vorp"] != "UNK" else "NR"
    s = sus.get((r["checkpoint"], r["internal_id"]))
    r["sustain_depth"] = s["sustain_depth"] if s else "UNK"
    r["sustain_kit_delta"] = s["sustain_kit_delta"] if s else "UNK"

dist = collections.Counter(r["tier"] for r in rows)
tot = len(rows)
print("TIER DISTRIBUTION (curve not forced)")
for t in ["S+","S","A","B","C","D","F","NR"]:
    print(f"   {t:3s} {dist[t]:7d}  {100*dist[t]/tot:5.1f}%")

# ---- primary role per (form, checkpoint), hybrids named
byfc = collections.defaultdict(list)
for r in scored: byfc[(r["checkpoint"], r["internal_id"])].append(r)
prim = {}
for k, v in byfc.items():
    v.sort(key=lambda x: -x["role_fit"])
    hyb = [x["role"] for x in v[1:3] if v[0]["role_fit"] - x["role_fit"] <= 0.05]
    prim[k] = (v[0], hyb, [x["role"] for x in v[:3]])

# ---- lineage aggregation with the dead-weight penalty
lin = collections.defaultdict(dict)
for (cp, iid), (bestr, hyb, top3) in prim.items():
    lin[sp[iid]["lineage_id"]][int(cp)] = (iid, bestr["vorp"], bestr["role"])
lin_rows = []
for lid, percp in lin.items():
    cps = sorted(percp)
    med = statistics.median([percp[c][1] for c in cps])
    raw = sum(percp[c][1] for c in cps) / len(cps)
    pen = 0.0
    for c in cps:
        if percp[c][1] < 0:                       # stuck in a form below replacement
            pen += DEADWEIGHT * abs(percp[c][1]) / len(cps)
    adj = raw - pen
    online = next((c for c in cps if percp[c][1] >= 0), None)
    lin_rows.append(dict(lineage_id=lid, checkpoints=len(cps), raw_mean_vorp=round(raw,4),
        dead_weight_penalty=round(pen,4), lineage_vorp=round(adj,4),
        comes_online_at=online if online is not None else "never",
        forms=",".join(sorted({sp[percp[c][0]]["form_key"] for c in cps}))))
L("V3_lineage", "INFO",
  f"{len(lin_rows)} lineages aggregated; dead-weight penalty {DEADWEIGHT} applied to every "
  f"checkpoint the line spends below replacement. Mean penalty "
  f"{sum(r['dead_weight_penalty'] for r in lin_rows)/len(lin_rows):.4f}")

# ---- INVARIANTS
rec = [prim[k][0] for k in prim]                  # the recommended build per (form, checkpoint)
def share(counter):
    n = sum(counter.values()); return max(counter.values())/n, counter.most_common(1)[0][0], n
i1, i1w, n1 = share(collections.Counter(r["ceiling_item"] for r in rec))
i2, i2w, _  = share(collections.Counter(r.get("nature","UNK") for r in rec))
moves = collections.Counter(m for r in rec for m in r["moves"].split(","))
i7 = max(moves.values())/len(rec); i7w = moves.most_common(1)[0][0]

# I3: mean |r| between VORP and BST within each (checkpoint, role)
def pearson(xs, ys):
    n=len(xs)
    if n<3: return None
    mx,my=sum(xs)/n,sum(ys)/n
    num=sum((a-mx)*(b-my) for a,b in zip(xs,ys))
    dx=sum((a-mx)**2 for a in xs)**.5; dy=sum((b-my)**2 for b in ys)**.5
    return num/(dx*dy) if dx and dy else None
cells=collections.defaultdict(list)
for r in scored: cells[(r["checkpoint"], r["role"])].append(r)
N_FLOOR = 20
rs, small = [], []
for k,v in cells.items():
    c=pearson([x["vorp"] for x in v],[int(sp[x["internal_id"]]["bst"]) for x in v])
    if c is None: continue
    (rs if len(v) >= N_FLOOR else small).append((abs(c), k, len(v)))
i3=sum(x[0] for x in rs)/len(rs)
i3_small=sum(x[0] for x in small)/len(small) if small else 0
worst=sorted(rs, reverse=True)[:5]
L("INV_I3_nfloor","INFO",
  f"I3 is a mean of within-cell correlations, so cells with too few builds are noise rather than "
  f"evidence. Cells with n<{N_FLOOR} are excluded from the mean and reported separately: "
  f"{len(small)} excluded (their mean |r| {i3_small:.3f}), {len(rs)} retained.")

# I4: every (checkpoint, role) has >=3 builds within 10% of the leader
i4fail=[]
for k,v in cells.items():
    lead=max(x["role_fit"] for x in v)
    if sum(1 for x in v if x["role_fit"] >= lead*0.9) < 3: i4fail.append((k, len(v)))

print(f"\nINVARIANTS  (recommended builds n={len(rec)})")
print(f"   I1 item share      {i1:.4f}  <=0.25   {'PASS' if i1<=.25 else 'FAIL'}   worst {i1w}")
print(f"   I2 nature share    {i2:.4f}  <=0.20   {'PASS' if i2<=.20 else 'FAIL'}   worst {i2w}")
print(f"   I3 mean|r| vs BST  {i3:.4f}  <=0.60   {'PASS' if i3<=.60 else 'FAIL'}  "
      f"(n>={N_FLOOR}, {len(rs)} cells; {len(small)} small cells excluded, their mean {i3_small:.3f})")
for a,k,n in worst: print(f"        worst cell cp{k[0]} {k[1]:18s} r={a:.3f} n={n}")
print(f"   I4 thin cells      {len(i4fail)} of {len(cells)}   {'PASS' if not i4fail else 'FAIL'}")
print(f"   I7 move share      {i7:.4f}  <=0.30   {'PASS' if i7<=.30 else 'FAIL'}   worst {i7w}")

for nm,val,thr,ok,extra in [("I1",i1,.25,i1<=.25,i1w),("I2",i2,.20,i2<=.20,i2w),
                            ("I3",i3,.60,i3<=.60,""),("I4",len(i4fail),0,not i4fail,""),
                            ("I7",i7,.30,i7<=.30,i7w)]:
    L(f"INV_{nm}", "INFO" if ok else "WARN",
      f"{'PASS' if ok else 'FAIL'} — observed {val} against threshold {thr} {extra}")

# ---- export
cols=["checkpoint","internal_id","form_key","lineage_id","role","role_family","track","tier",
      "vorp","replacement","role_fit","S","T","Y","F","ceiling_margin","floor_margin","roi",
      "ceiling_item","item_dependence","setup_move","nature","switchin_safe_rate","sustain_depth",
      "sustain_kit_delta","moves","confidence"]
with open(f"{OUT}/05_valuation.tsv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=cols,delimiter="\t",lineterminator="\n",extrasaction="ignore")
    w.writeheader(); w.writerows(rows)
with open(f"{OUT}/05b_lineage.tsv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(lin_rows[0]),delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(sorted(lin_rows,key=lambda r:-r["lineage_vorp"]))
json.dump(log, open(f"{OUT}/INT_integrity_log_phase5.json","w"), indent=1)
print(f"\nwrote 05_valuation.tsv {len(rows)} rows; 05b_lineage.tsv {len(lin_rows)} lineages")
print("\ntop lineages by dead-weight-adjusted VORP:")
for r in sorted(lin_rows,key=lambda r:-r["lineage_vorp"])[:8]:
    print(f"   {r['forms'][:44]:46s} vorp {r['lineage_vorp']:+.3f} "
          f"(raw {r['raw_mean_vorp']:+.3f} penalty {r['dead_weight_penalty']:.3f}) online cp{r['comes_online_at']}")
